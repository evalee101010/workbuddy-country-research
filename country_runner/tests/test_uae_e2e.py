import tempfile
import unittest
from pathlib import Path

import yaml

from country_runner.build import build_run
from country_runner.csvio import read_csv, read_header, write_csv
from country_runner.discovery import discover_run
from country_runner.manifest import ManifestError, initialize_run, load_manifest
from country_runner.migrate_uae import migrate_uae
from country_runner.pilot import pilot_run
from country_runner.validation import validate_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"
LEGACY_FIXTURE = RUNNER_ROOT / "tests" / "fixtures" / "uae-legacy"


class UaeEndToEndTests(unittest.TestCase):
    def test_uae_country_run_reaches_warn_build_and_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runs_root = Path(temp)
            run_dir = initialize_run(
                country_code="AE",
                run_id="uae-e2e",
                runs_root=runs_root,
                config_root=RUNNER_ROOT / "config",
                templates_root=RUNNER_ROOT / "templates",
                researcher="Demo Researcher",
            )
            discover = discover_run(run_dir, RUNNER_ROOT / "config")
            self.assertGreater(discover["queries"]["A"], 0)
            all_query_scopes = set()
            for path in (run_dir / "queries").glob("*.csv"):
                rows = read_csv(path)
                for row in rows:
                    all_query_scopes.add(row["scope_name"])
                    if row["language_role"] == "core":
                        row["status"] = "Completed"
                        row["results_inspected"] = "1"
                        row["valid_results"] = "0"
                    if row["source_name"] in {"Trustpilot", "LinkedIn public posts"} and row["query_group"] in {
                        "country-core-1", "country-core-2"
                    }:
                        row["valid_results"] = "2"
                write_csv(path, read_header(path), rows)
            self.assertTrue({
                "Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain",
                "Ras Al Khaimah", "Fujairah",
            }.issubset(all_query_scopes))

            registry = read_csv(run_dir / "02-source-discovery.csv")
            by_name = {row["source_name"]: row["source_id"] for row in registry}
            pilot_path = run_dir / "03-channel-fit-pilot.csv"
            pilots = []
            for name in ("Trustpilot", "LinkedIn public posts"):
                row = {field: "" for field in read_header(pilot_path)}
                row.update({
                    "source_id": by_name[name],
                    "included_count": "4",
                    "high_geo_count": "2",
                    "medium_geo_count": "2",
                    "mainstream_task_count": "3",
                    "original_text_available": "Yes",
                    "date_available": "Yes",
                    "repeatable_discovery": "Yes",
                    "reviewer": "Demo Gate A Reviewer",
                    "captured_at": "2026-09-03T00:00:00+00:00",
                })
                pilots.append(row)
            write_csv(pilot_path, read_header(pilot_path), pilots)
            self.assertEqual(pilot_run(run_dir)["status"], "source_plan_pending")

            plan_path = run_dir / "04-approved-source-plan.yml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan.update({
                "approval_status": "approved",
                "approved_by": "Demo Gate A Reviewer",
                "approved_at": "2026-09-03T01:00:00+00:00",
                "approval_note": "Simulated approval for end-to-end workflow acceptance.",
            })
            plan["streams"]["B"]["documented_gap"] = (
                "Legacy UAE pilot did not independently code the local-needs evidence line."
            )
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertEqual(pilot_run(run_dir)["status"], "source_plan_approved")

            migration = migrate_uae(LEGACY_FIXTURE, run_dir)
            self.assertEqual(migration["output_rows"], {"raw": 3, "A": 1, "C": 2})
            for filename in ("A-competitor-feedback.csv", "C-kol-koc-content.csv"):
                path = run_dir / "evidence" / filename
                rows = read_csv(path)
                rows[0]["headline_evidence"] = "Yes"
                if filename.startswith("C-"):
                    rows[0]["inclusion_status"] = "Included"
                write_csv(path, read_header(path), rows)

            first_validation = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(first_validation["status"], "validation_block")
            self.assertIn(
                "reviewer_signature_missing",
                {issue["code"] for issue in first_validation["issues"]},
            )
            audit_path = run_dir / "review" / "evidence-audit.csv"
            audit = read_csv(audit_path)
            for row in audit:
                if row["required_review"] == "Yes":
                    row.update({
                        "review_status": "Reviewed-pass",
                        "reviewer": "Demo Gate B Reviewer (simulated)",
                        "reviewed_at": "2026-09-03T02:00:00+00:00",
                        "provenance_ok": "Yes",
                        "translation_ok": "Yes",
                        "geo_ok": "Yes",
                        "audience_ok": "Yes",
                        "dedup_ok": "Yes",
                        "issue_level": "PASS",
                    })
            write_csv(audit_path, read_header(audit_path), audit)
            second_validation = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(second_validation["status"], "validation_warn", second_validation["issues"])
            codes = {issue["code"] for issue in second_validation["issues"]}
            self.assertIn("subnational_gap", codes)
            self.assertIn("stream_documented_gap", codes)

            def fake_xlsx(_run_dir, output_path):
                Path(output_path).write_bytes(b"fake xlsx for state-machine acceptance")

            built = build_run(run_dir, RUNNER_ROOT / "config", xlsx_builder=fake_xlsx)
            self.assertEqual(built["status"], "frozen")
            self.assertEqual(load_manifest(run_dir)["state"], "frozen")
            with self.assertRaises(ManifestError):
                build_run(run_dir, RUNNER_ROOT / "config", xlsx_builder=fake_xlsx)

            new_run = initialize_run(
                country_code="AE",
                run_id="uae-next-run",
                runs_root=runs_root,
                config_root=RUNNER_ROOT / "config",
                templates_root=RUNNER_ROOT / "templates",
                researcher="Another Researcher",
            )
            self.assertEqual(load_manifest(new_run)["state"], "initialized")


if __name__ == "__main__":
    unittest.main()
