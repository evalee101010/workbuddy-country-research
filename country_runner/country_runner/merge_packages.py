import csv
import json
import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from .data_package import sha256_file, verify_package
from .manifest import ManifestError, utc_now


MERGE_TABLES = {
    "02-source-discovery.csv": ("sources.csv", "source_id"),
    "03-channel-fit-pilot.csv": ("channel-pilot.csv", "source_id"),
    "evidence/raw-discovery-log.csv": ("raw-discovery-log.csv", "content_id"),
    "evidence/A-competitor-feedback.csv": ("A-competitor-feedback.csv", "evidence_id"),
    "evidence/B-local-work-needs.csv": ("B-local-work-needs.csv", "evidence_id"),
    "evidence/C-kol-koc-content.csv": ("C-kol-koc-content.csv", "evidence_id"),
    "queries/A-competitor-queries.csv": ("A-competitor-queries.csv", "query_id"),
    "queries/B-local-needs-queries.csv": ("B-local-needs-queries.csv", "query_id"),
    "queries/C-kol-koc-queries.csv": ("C-kol-koc-queries.csv", "query_id"),
    "quality/coverage-matrix.csv": ("coverage-matrix.csv", ""),
}


def _read_csv(path: Path) -> tuple:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_zip(source_root: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(source_root.parent).as_posix())
    temporary.replace(destination)


def merge_country_packages(zip_paths: List[Path], output_dir: Path) -> dict:
    if len(zip_paths) < 2:
        raise ManifestError("merge requires at least two country package ZIPs")
    output_dir = Path(output_dir)
    zip_destination = Path(str(output_dir) + ".zip")
    if output_dir.exists():
        raise ManifestError(f"refusing to overwrite merge output: {output_dir}")
    if zip_destination.exists():
        raise ManifestError(f"refusing to overwrite merged ZIP: {zip_destination}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="workbuddy-country-merge-") as temporary:
        temp_root = Path(temporary)
        packages = []
        for index, zip_path in enumerate(zip_paths):
            extraction = temp_root / f"package-{index:03d}"
            extraction.mkdir()
            package_root, manifest = verify_package(Path(zip_path), extraction)
            packages.append({
                "zip_path": Path(zip_path),
                "root": package_root,
                "manifest": manifest,
            })

        format_versions = {item["manifest"].get("package_format_version") for item in packages}
        schema_versions = {item["manifest"].get("schema_version") for item in packages}
        if len(format_versions) != 1 or len(schema_versions) != 1:
            raise ManifestError("country packages use incompatible package/schema versions")
        keys = [
            (item["manifest"].get("country_iso2"), item["manifest"].get("run_id"))
            for item in packages
        ]
        if len(keys) != len(set(keys)):
            raise ManifestError("duplicate country/run package supplied")

        staging = temp_root / "merged-output"
        staging.mkdir()
        tables_dir = staging / "tables"
        rows_by_table: Dict[str, List[dict]] = {}
        global_ids: Dict[str, Dict[str, str]] = defaultdict(dict)

        for source_relative, (destination_name, id_field) in MERGE_TABLES.items():
            baseline_header: List[str] = []
            merged_rows: List[dict] = []
            for package in packages:
                path = package["root"] / source_relative
                header, rows = _read_csv(path)
                if not baseline_header:
                    baseline_header = header
                elif header != baseline_header:
                    raise ManifestError(f"schema mismatch across packages: {source_relative}")
                country = package["manifest"]["country_iso2"]
                run_id = package["manifest"]["run_id"]
                package_key = f"{country}/{run_id}"
                for row in rows:
                    if id_field:
                        identifier = row.get(id_field, "")
                        previous = global_ids[id_field].get(identifier)
                        if identifier and previous and previous != package_key:
                            raise ManifestError(
                                f"cross-package {id_field} conflict: {identifier} in {previous} and {package_key}"
                            )
                        if identifier:
                            global_ids[id_field][identifier] = package_key
                    merged = {
                        "package_country_iso2": country,
                        "package_run_id": run_id,
                    }
                    merged.update(row)
                    merged_rows.append(merged)
            output_header = ["package_country_iso2", "package_run_id", *baseline_header]
            _write_csv(tables_dir / destination_name, output_header, merged_rows)
            rows_by_table[destination_name] = merged_rows

        duplicates = defaultdict(list)
        for row in rows_by_table["raw-discovery-log.csv"]:
            canonical = str(row.get("canonical_url", "")).strip()
            if canonical:
                duplicates[("canonical_url", canonical)].append(row)
            platform_id = str(row.get("platform_content_id", "")).strip()
            source_name = str(row.get("source_name", "")).strip()
            if platform_id and source_name:
                duplicates[("platform_content_id", f"{source_name}:{platform_id}")].append(row)
        duplicate_rows = []
        seen_memberships = set()
        for (key_type, key_value), rows in sorted(duplicates.items()):
            countries = sorted({row["package_country_iso2"] for row in rows})
            if len(countries) < 2:
                continue
            membership = tuple(sorted(
                (row["package_country_iso2"], row.get("content_id", "")) for row in rows
            ))
            if membership in seen_memberships:
                continue
            seen_memberships.add(membership)
            duplicate_rows.append({
                "duplicate_key_type": key_type,
                "duplicate_key": key_value,
                "canonical_url": key_value if key_type == "canonical_url" else "",
                "countries": "|".join(countries),
                "content_ids": "|".join(sorted(row.get("content_id", "") for row in rows)),
                "package_runs": "|".join(sorted({
                    f"{row['package_country_iso2']}/{row['package_run_id']}" for row in rows
                })),
                "action": "Retained; review as regional, migration-corridor or search-leakage content.",
            })
        _write_csv(
            staging / "cross-country-duplicates.csv",
            [
                "duplicate_key_type", "duplicate_key", "canonical_url", "countries",
                "content_ids", "package_runs", "action",
            ],
            duplicate_rows,
        )

        index_rows = []
        for package in packages:
            manifest = package["manifest"]
            index_rows.append({
                "country_iso2": manifest["country_iso2"],
                "country_iso3": manifest["country_iso3"],
                "run_id": manifest["run_id"],
                "researcher": manifest.get("researcher", ""),
                "window_start": (manifest.get("research_window") or {}).get("start", ""),
                "window_end": (manifest.get("research_window") or {}).get("end", ""),
                "validation_status": manifest.get("validation_status", ""),
                "package_file": package["zip_path"].name,
                "package_sha256": sha256_file(package["zip_path"]),
            })
        _write_csv(
            staging / "country-pack-index.csv",
            [
                "country_iso2", "country_iso3", "run_id", "researcher", "window_start",
                "window_end", "validation_status", "package_file", "package_sha256",
            ],
            index_rows,
        )

        warnings = []
        for package in packages:
            key = f"{package['manifest']['country_iso2']}/{package['manifest']['run_id']}"
            for warning in package["manifest"].get("warnings", []):
                warnings.append({"package": key, **warning})
        warning_lines = [
            "# 国家包合并告警", "",
            f"合并 {len(packages)} 个国家包；发现 {len(duplicate_rows)} 组跨国 URL/平台内容 ID 重复。", "",
            "跨国重复未自动删除。各包原始 WARN 仍保留在 `merged-manifest.json`。", "",
        ]
        (staging / "merge-warnings.md").write_text("\n".join(warning_lines), encoding="utf-8")

        merged_manifest = {
            "merged_format_version": 1,
            "created_at": utc_now(),
            "package_format_version": next(iter(format_versions)),
            "schema_version": next(iter(schema_versions)),
            "country_package_count": len(packages),
            "countries": sorted({item["manifest"]["country_iso2"] for item in packages}),
            "table_counts": {name: len(rows) for name, rows in sorted(rows_by_table.items())},
            "cross_country_duplicate_groups": len(duplicate_rows),
            "warnings": warnings,
        }
        (staging / "merged-manifest.json").write_text(
            json.dumps(merged_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        shutil.move(str(staging), str(output_dir))

    _write_zip(output_dir, zip_destination)
    return {
        "status": "merged",
        "output_dir": str(output_dir),
        "output_zip": str(zip_destination),
        "country_package_count": len(zip_paths),
        "cross_country_duplicate_groups": len(duplicate_rows),
    }
