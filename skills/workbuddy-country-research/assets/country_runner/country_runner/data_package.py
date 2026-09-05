import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import List, Tuple

from .internal_validation import validate_internal_run
from .manifest import ManifestError, load_manifest, utc_now


PACKAGE_FORMAT_VERSION = 1
RUNNER_VERSION = "1.0.0-internal"

PACKAGE_FILES = {
    "00-run-manifest.yml": "00-run-manifest.yml",
    "01-country-context.md": "01-country-context.md",
    "02-source-discovery.csv": "02-source-discovery.csv",
    "03-channel-fit-pilot.csv": "03-channel-fit-pilot.csv",
    "04-source-plan.yml": "04-approved-source-plan.yml",
    "05-collection-funnel.md": "05-collection-funnel.md",
    "evidence/raw-discovery-log.csv": "evidence/raw-discovery-log.csv",
    "evidence/A-competitor-feedback.csv": "evidence/A-competitor-feedback.csv",
    "evidence/B-local-work-needs.csv": "evidence/B-local-work-needs.csv",
    "evidence/C-kol-koc-content.csv": "evidence/C-kol-koc-content.csv",
    "queries/A-competitor-queries.csv": "queries/A-competitor-queries.csv",
    "queries/B-local-needs-queries.csv": "queries/B-local-needs-queries.csv",
    "queries/C-kol-koc-queries.csv": "queries/C-kol-koc-queries.csv",
    "quality/coverage-matrix.csv": "quality/coverage-matrix.csv",
    "quality/gaps-and-biases.md": "quality/gaps-and-biases.md",
    "quality/structural-validation.json": "quality/structural-validation.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> List[dict]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _coverage_summary(run_dir: Path) -> dict:
    sources = _read_csv(Path(run_dir) / "02-source-discovery.csv")
    raw = [
        row for row in _read_csv(Path(run_dir) / "evidence" / "raw-discovery-log.csv")
        if row.get("inclusion_status") == "Included"
    ]
    return {
        "source_families": dict(sorted(Counter(row.get("source_family") or "Unknown" for row in sources).items())),
        "content_languages": dict(sorted(Counter(row.get("content_language") or "Unknown" for row in raw).items())),
        "admin1": dict(sorted(Counter(row.get("admin1_name") or "national_or_unknown" for row in raw).items())),
        "audience_roles": dict(sorted(Counter(row.get("audience_role") or "Unknown" for row in raw).items())),
    }


def _copy_package_files(run_dir: Path, package_root: Path) -> None:
    for destination, source in PACKAGE_FILES.items():
        source_path = Path(run_dir) / source
        if not source_path.exists():
            raise ManifestError(f"required package file not found: {source_path}")
        destination_path = Path(package_root) / destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def _file_manifest(package_root: Path) -> List[dict]:
    output = []
    for path in sorted(item for item in Path(package_root).rglob("*") if item.is_file()):
        if path.name == "package-manifest.json":
            continue
        output.append({
            "path": path.relative_to(package_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return output


def _write_zip(source_root: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(source_root.parent).as_posix())
    temporary.replace(destination)


def package_country_run(
    run_dir: Path,
    config_root: Path,
    templates_root: Path,
    output_dir: Path,
) -> dict:
    run_dir = Path(run_dir)
    validation = validate_internal_run(run_dir, Path(config_root), Path(templates_root))
    if validation["status"] == "internal_validation_block":
        block_count = validation.get("severity_counts", {}).get("BLOCK", 0)
        raise ManifestError(f"internal packaging blocked by {block_count} structural issue(s)")

    manifest = load_manifest(run_dir)
    package_name = f"workbuddy-country-data-{manifest['country_iso2']}-{manifest['run_id']}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{package_name}.zip"
    if destination.exists():
        raise ManifestError(f"refusing to overwrite existing package: {destination}")

    with tempfile.TemporaryDirectory(prefix="workbuddy-country-package-") as temporary:
        package_root = Path(temporary) / package_name
        package_root.mkdir()
        _copy_package_files(run_dir, package_root)
        created_at = utc_now()
        package_manifest = {
            "package_format_version": PACKAGE_FORMAT_VERSION,
            "package_name": package_name,
            "internal_use_only": True,
            "created_at": created_at,
            "country_iso2": manifest["country_iso2"],
            "country_iso3": manifest["country_iso3"],
            "run_id": manifest["run_id"],
            "researcher": manifest.get("researcher", "Unknown"),
            "research_window": manifest.get("research_window", {}),
            "schema_version": 1,
            "config_version": manifest.get("config_version", 1),
            "codebook_version": manifest.get("codebook_version", 1),
            "runner_version": RUNNER_VERSION,
            "validation_status": validation["status"],
            "counts": validation["counts"],
            "coverage": _coverage_summary(run_dir),
            "completeness_labels": validation.get("completeness_labels", []),
            "warnings": [
                issue for issue in validation["issues"] if issue.get("severity") in {"WARN", "INFO"}
            ],
            "files": _file_manifest(package_root),
        }
        _atomic_json(package_root / "package-manifest.json", package_manifest)
        _write_zip(package_root, destination)

    _atomic_json(run_dir / "package-manifest.json", package_manifest)
    return {
        "status": "packaged_internal_data",
        "package": str(destination),
        "package_sha256": sha256_file(destination),
        "validation_status": validation["status"],
        "counts": validation["counts"],
    }


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = Path(destination).resolve()
    seen = set()
    for member in archive.infolist():
        normalized = PurePosixPath(member.filename)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ManifestError(f"unsafe ZIP member path: {member.filename}")
        if member.filename in seen:
            raise ManifestError(f"duplicate ZIP member path: {member.filename}")
        seen.add(member.filename)
        if ((member.external_attr >> 16) & 0o170000) == 0o120000:
            raise ManifestError(f"symbolic links are not allowed in package ZIPs: {member.filename}")
        resolved = (root / member.filename).resolve()
        if root != resolved and root not in resolved.parents:
            raise ManifestError(f"unsafe ZIP member path: {member.filename}")
    archive.extractall(root)


def verify_package(zip_path: Path, extraction_root: Path) -> Tuple[Path, dict]:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise ManifestError(f"package not found: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path) as archive:
            _safe_extract(archive, extraction_root)
    except zipfile.BadZipFile as error:
        raise ManifestError(f"invalid ZIP package: {zip_path}") from error

    manifests = list(Path(extraction_root).rglob("package-manifest.json"))
    if len(manifests) != 1:
        raise ManifestError(f"package must contain exactly one package-manifest.json: {zip_path}")
    manifest_path = manifests[0]
    package_root = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ManifestError(f"invalid package manifest: {zip_path}") from error
    if manifest.get("package_format_version") != PACKAGE_FORMAT_VERSION:
        raise ManifestError(f"unsupported package format: {manifest.get('package_format_version')}")
    required_manifest_fields = {
        "package_name", "country_iso2", "country_iso3", "run_id", "schema_version", "files",
    }
    missing_fields = sorted(required_manifest_fields - set(manifest))
    if missing_fields:
        raise ManifestError("package manifest is missing: " + ", ".join(missing_fields))
    if manifest.get("internal_use_only") is not True:
        raise ManifestError("package is not marked internal_use_only")
    if not isinstance(manifest.get("files"), list):
        raise ManifestError("package manifest files must be a list")
    if manifest.get("package_name") != package_root.name:
        raise ManifestError("package root folder does not match package_name")
    file_paths = [item.get("path") for item in manifest["files"]]
    if len(file_paths) != len(set(file_paths)):
        raise ManifestError("package manifest contains duplicate file paths")
    for item in manifest["files"]:
        relative = item.get("path", "")
        normalized = PurePosixPath(relative)
        if not relative or normalized.is_absolute() or ".." in normalized.parts:
            raise ManifestError(f"unsafe package manifest path: {relative}")
        path = package_root / relative
        if not path.exists() or not path.is_file():
            raise ManifestError(f"package file missing: {relative}")
        if path.stat().st_size != item.get("bytes"):
            raise ManifestError(f"package file size mismatch: {relative}")
        if sha256_file(path) != item.get("sha256"):
            raise ManifestError(f"package file hash mismatch: {relative}")
    expected = {item.get("path") for item in manifest["files"]}
    actual = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file() and path.name != "package-manifest.json"
    }
    if expected != actual:
        raise ManifestError("package file list does not match archive contents")
    return package_root, manifest
