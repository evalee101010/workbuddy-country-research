import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from country_runner.data_package import package_country_run, verify_package
from country_runner.discovery import discover_run
from country_runner.internal_validation import validate_internal_run
from country_runner.manifest import ManifestError, initialize_run
from country_runner.merge_packages import merge_country_packages


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"
CONFIG_ROOT = RUNNER_ROOT / "config"
TEMPLATES_ROOT = RUNNER_ROOT / "templates"


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows):
    with path.open(encoding="utf-8", newline="") as handle:
        fieldnames = next(csv.reader(handle))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def blank_row(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return {field: "" for field in next(csv.reader(handle))}


def make_ready_run(root: Path, country: str, run_id: str, shared_url: bool = False) -> Path:
    run_dir = initialize_run(
        country_code=country,
        run_id=run_id,
        runs_root=root / "runs",
        config_root=CONFIG_ROOT,
        templates_root=TEMPLATES_ROOT,
        researcher=f"Researcher {country}",
        window_start="2026-01-01",
        window_end="2026-08-31",
    )
    discover_run(run_dir, CONFIG_ROOT)
    manifest = yaml.safe_load((run_dir / "00-run-manifest.yml").read_text(encoding="utf-8"))
    iso3 = manifest["country_iso3"]
    registry = read_rows(run_dir / "02-source-discovery.csv")

    selected = {}
    for stream in ("A", "B", "C"):
        candidates = [
            row for row in registry
            if stream in row["candidate_evidence_streams"].split("|")
            and row["local_role"] != "global_technical"
            and row["local_role"] != "recruitment_only"
        ]
        selected[stream] = candidates[0]

    pilot_path = run_dir / "03-channel-fit-pilot.csv"
    pilot_rows = []
    selected_ids = {row["source_id"] for row in selected.values()}
    for source in registry:
        row = blank_row(pilot_path)
        row.update({
            "source_id": source["source_id"],
            "channel": source["source_name"],
            "source_family": source["source_family"],
            "evidence_streams": source["candidate_evidence_streams"],
            "access_status": source["access_status"],
            "pilot_recommendation": "Core" if source["source_id"] in selected_ids else "Reject",
            "final_role": "Core" if source["source_id"] in selected_ids else "Reject",
            "decision_reason": "Deterministic internal package fixture.",
            "captured_at": "2026-09-01T00:00:00+00:00",
        })
        pilot_rows.append(row)
    write_rows(pilot_path, pilot_rows)

    plan = {
        "version": 1,
        "run_id": run_id,
        "country_iso2": country,
        "generated_at": "2026-09-01T00:00:00+00:00",
        "streams": {
            stream: {
                "core": [selected[stream]["source_id"]],
                "supplement": [],
                "documented_gap": "",
            }
            for stream in ("A", "B", "C")
        },
        "source_decisions": [
            {
                "source_id": source["source_id"],
                "source_name": source["source_name"],
                "role": "Core" if source["source_id"] in selected_ids else "Reject",
                "streams": source["candidate_evidence_streams"].split("|"),
                "decision_reason": "Deterministic internal package fixture.",
            }
            for source in registry
        ],
        "rejected_sources": [
            source["source_id"] for source in registry if source["source_id"] not in selected_ids
        ],
    }
    (run_dir / "04-approved-source-plan.yml").write_text(
        yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    chosen_queries = {}
    query_files = {
        "A": "A-competitor-queries.csv",
        "B": "B-local-needs-queries.csv",
        "C": "C-kol-koc-queries.csv",
    }
    for stream, filename in query_files.items():
        path = run_dir / "queries" / filename
        rows = read_rows(path)
        chosen = next(row for row in rows if row["source_name"] == selected[stream]["source_name"])
        chosen_queries[stream] = chosen
        for row_index, row in enumerate(rows):
            row["status"] = "Completed"
            row["results_inspected"] = "1"
            row["valid_results"] = "1" if row["query_id"] == chosen["query_id"] else "0"
            row["notes"] = "Executed in fixture; no unrecorded hits."
            if stream == "A" and row_index == 0:
                row["notes"] += " saturation_batch_1; new_unique=0; new_dimensions=0."
            if stream == "A" and row_index == 1:
                row["notes"] += " saturation_batch_2; new_unique=0; new_dimensions=0."
        write_rows(path, rows)

    raw_path = run_dir / "evidence" / "raw-discovery-log.csv"
    raw_rows = []
    evidence_rows = {"A": [], "B": [], "C": []}
    evidence_files = {
        "A": "A-competitor-feedback.csv",
        "B": "B-local-work-needs.csv",
        "C": "C-kol-koc-content.csv",
    }
    for index, stream in enumerate(("A", "B", "C"), 1):
        source = selected[stream]
        query = chosen_queries[stream]
        url = "https://example.org/shared-item" if shared_url and stream == "A" else (
            f"https://example.org/{country.lower()}/{stream.lower()}-{index}"
        )
        content_id = f"CNT-{iso3}-{index:03d}"
        raw = blank_row(raw_path)
        raw.update({
            "content_id": content_id,
            "run_id": run_id,
            "source_id": source["source_id"],
            "source_type": source["source_family"],
            "source_name": source["source_name"],
            "source_url": source["source_url"],
            "item_url": url,
            "canonical_url": url,
            "author_alias": "public-user",
            "published_at": "2026-08-01",
            "published_at_raw": "2026-08-01",
            "date_confidence": "Exact",
            "captured_at": "2026-09-01T00:00:00+00:00",
            "query_hit_ids": query["query_id"],
            "query_language": query["query_language"],
            "content_language": "en",
            "original_text": f"Public evidence for stream {stream} about a mainstream work task.",
            "original_text_translation_cn": f"证据流 {stream} 的公开工作任务证据。",
            "context_note": "Minimal public excerpt retained for testing.",
            "country_iso3": iso3,
            "country_or_region": country,
            "admin1_name": query.get("admin1_name") or "National",
            "admin1_confidence": "Medium",
            "geo_evidence": f"The item explicitly names {country}.",
            "country_confidence": "High",
            "scope_level": "country",
            "scope_name": iso3,
            "discovery_round": "1",
            "country_assignment_status": "exact_country",
            "audience_role": query["audience_role"],
            "technical_level": "Non-technical",
            "source_audience_bias": source["audience_profile"],
            "inclusion_status": "Included",
            "review_status": "Pending",
            "capture_mode": "public_manual",
        })
        raw_rows.append(raw)

        evidence_path = run_dir / "evidence" / evidence_files[stream]
        evidence = blank_row(evidence_path)
        evidence.update({key: value for key, value in raw.items() if key in evidence})
        evidence.update({
            "evidence_id": f"EVD-{iso3}-{index:03d}",
            "content_id": content_id,
            "evidence_stream": stream,
            "query_id": query["query_id"],
            "headline_evidence": f"Fixture evidence {stream}",
            "normalized_theme": "office_productivity",
        })
        if stream == "A":
            evidence.update({"product": "ChatGPT agent", "job_to_be_done": "Draft a report"})
        elif stream == "B":
            evidence.update({"work_task": "reporting", "pain_point": "manual repetition"})
        else:
            evidence.update({
                "creator_name": "Public Creator",
                "creator_type": "KOC",
                "content_format": "video",
                "views_visible": "1000",
                "metric_captured_at": "2026-09-01T00:00:00+00:00",
            })
        evidence_rows[stream].append(evidence)

    write_rows(raw_path, raw_rows)
    for stream, filename in evidence_files.items():
        write_rows(run_dir / "evidence" / filename, evidence_rows[stream])
    return run_dir


class InternalPackageTests(unittest.TestCase):
    def test_validate_and_package_country_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = make_ready_run(root, "AE", "ae-fixture")
            result = validate_internal_run(run_dir, CONFIG_ROOT, TEMPLATES_ROOT)
            self.assertNotEqual(result["status"], "internal_validation_block", result["issues"])
            packaged = package_country_run(
                run_dir, CONFIG_ROOT, TEMPLATES_ROOT, root / "packages"
            )
            zip_path = Path(packaged["package"])
            self.assertTrue(zip_path.exists())
            extraction = root / "extract"
            package_root, manifest = verify_package(zip_path, extraction)
            self.assertTrue(manifest["internal_use_only"])
            self.assertEqual(manifest["counts"]["included_evidence"], 3)
            self.assertTrue((package_root / "quality" / "structural-validation.json").exists())

    def test_duplicate_evidence_id_across_streams_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = make_ready_run(root, "AE", "duplicate-fixture")
            a_rows = read_rows(run_dir / "evidence" / "A-competitor-feedback.csv")
            b_path = run_dir / "evidence" / "B-local-work-needs.csv"
            b_rows = read_rows(b_path)
            b_rows[0]["evidence_id"] = a_rows[0]["evidence_id"]
            write_rows(b_path, b_rows)
            result = validate_internal_run(run_dir, CONFIG_ROOT, TEMPLATES_ROOT)
            self.assertEqual(result["status"], "internal_validation_block")
            self.assertIn(
                "duplicate_primary_id_across_streams",
                {issue["code"] for issue in result["issues"]},
            )

    def test_missing_saturation_or_limit_label_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = make_ready_run(root, "AE", "stop-basis-fixture")
            path = run_dir / "queries" / "A-competitor-queries.csv"
            rows = read_rows(path)
            for row in rows:
                row["notes"] = "Executed in fixture; no stopping basis recorded."
            write_rows(path, rows)
            result = validate_internal_run(run_dir, CONFIG_ROOT, TEMPLATES_ROOT)
            self.assertEqual(result["status"], "internal_validation_block")
            self.assertIn(
                "collection_stop_basis_missing",
                {issue["code"] for issue in result["issues"]},
            )

    def test_merge_two_country_packages_and_retain_cross_country_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package_paths = []
            for country in ("AE", "GB"):
                run_dir = make_ready_run(root / country, country, f"{country.lower()}-fixture", True)
                result = package_country_run(
                    run_dir, CONFIG_ROOT, TEMPLATES_ROOT, root / "packages"
                )
                package_paths.append(Path(result["package"]))
            merged = merge_country_packages(package_paths, root / "merged" / "country-data")
            self.assertEqual(merged["country_package_count"], 2)
            self.assertEqual(merged["cross_country_duplicate_groups"], 1)
            self.assertTrue(Path(merged["output_zip"]).exists())
            duplicate_rows = read_rows(
                Path(merged["output_dir"]) / "cross-country-duplicates.csv"
            )
            self.assertEqual(duplicate_rows[0]["countries"], "AE|GB")

    def test_tampered_country_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = make_ready_run(root, "AE", "tamper-fixture")
            result = package_country_run(
                run_dir, CONFIG_ROOT, TEMPLATES_ROOT, root / "packages"
            )
            original = Path(result["package"])
            extracted = root / "tampered-files"
            with zipfile.ZipFile(original) as archive:
                archive.extractall(extracted)
            data_file = next(extracted.rglob("A-competitor-feedback.csv"))
            data_file.write_text(data_file.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            tampered = root / "tampered.zip"
            package_root = next(path for path in extracted.iterdir() if path.is_dir())
            with zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in package_root.rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(extracted).as_posix())
            with self.assertRaises(ManifestError):
                verify_package(tampered, root / "tampered-extract")


if __name__ == "__main__":
    unittest.main()
