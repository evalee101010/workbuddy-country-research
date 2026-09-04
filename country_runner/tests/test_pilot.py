import csv
import tempfile
import unittest
from pathlib import Path

import yaml

from country_runner.discovery import discover_run
from country_runner.manifest import ManifestError, initialize_run, load_manifest
from country_runner.pilot import pilot_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_header(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


class PilotTests(unittest.TestCase):
    def make_run(self, temp: str) -> Path:
        run_dir = initialize_run(
            country_code="AE",
            run_id="pilot-demo",
            runs_root=Path(temp),
            config_root=RUNNER_ROOT / "config",
            templates_root=RUNNER_ROOT / "templates",
            researcher="Researcher",
        )
        discover_run(run_dir, RUNNER_ROOT / "config")
        return run_dir

    def seed_successful_trustpilot_pilot(self, run_dir: Path) -> str:
        registry = read_rows(run_dir / "02-source-discovery.csv")
        trustpilot_id = next(
            row["source_id"] for row in registry if row["source_name"] == "Trustpilot"
        )

        query_path = run_dir / "queries" / "A-competitor-queries.csv"
        queries = read_rows(query_path)
        groups_seen = set()
        for row in queries:
            if row["source_name"] != "Trustpilot" or row["query_group"] in groups_seen:
                continue
            row["status"] = "Completed"
            row["results_inspected"] = "10"
            row["valid_results"] = "3"
            groups_seen.add(row["query_group"])
            if len(groups_seen) == 2:
                break
        write_rows(query_path, queries)

        pilot_path = run_dir / "03-channel-fit-pilot.csv"
        header = read_header(pilot_path)
        seed = {field: "" for field in header}
        seed.update({
            "source_id": trustpilot_id,
            "high_geo_count": "2",
            "medium_geo_count": "1",
            "included_count": "3",
            "mainstream_task_count": "2",
            "original_text_available": "Yes",
            "date_available": "Yes",
            "repeatable_discovery": "Yes",
            "decision_reason": "Manual pilot verified provenance and local use context.",
            "reviewer": "Pilot Reviewer",
            "captured_at": "2026-09-03T00:00:00+00:00",
        })
        write_rows(pilot_path, [seed])
        return trustpilot_id

    def test_pilot_recommends_core_only_after_two_valid_query_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            trustpilot_id = self.seed_successful_trustpilot_pilot(run_dir)
            result = pilot_run(run_dir)

            self.assertEqual(result["status"], "source_plan_pending")
            self.assertEqual(load_manifest(run_dir)["state"], "source_plan_pending")
            rows = read_rows(run_dir / "03-channel-fit-pilot.csv")
            trustpilot = next(row for row in rows if row["source_id"] == trustpilot_id)
            self.assertEqual(trustpilot["pilot_recommendation"], "Core")
            self.assertEqual(trustpilot["query_groups_tested"], "2")
            self.assertEqual(trustpilot["inspected_count"], "20")

            plan = yaml.safe_load(
                (run_dir / "04-approved-source-plan.yml").read_text(encoding="utf-8")
            )
            self.assertIn(trustpilot_id, plan["streams"]["A"]["core"])
            self.assertEqual(plan["approval_status"], "pending")

    def test_global_technical_source_is_capped_at_supplement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            registry = read_rows(run_dir / "02-source-discovery.csv")
            github_id = next(row["source_id"] for row in registry if row["source_name"] == "GitHub")
            query_path = run_dir / "queries" / "A-competitor-queries.csv"
            queries = read_rows(query_path)
            groups_seen = set()
            for row in queries:
                if row["source_name"] == "GitHub" and row["query_group"] not in groups_seen:
                    row["status"] = "Completed"
                    row["results_inspected"] = "10"
                    row["valid_results"] = "5"
                    groups_seen.add(row["query_group"])
                    if len(groups_seen) == 2:
                        break
            write_rows(query_path, queries)

            pilot_path = run_dir / "03-channel-fit-pilot.csv"
            header = read_header(pilot_path)
            row = {field: "" for field in header}
            row.update({
                "source_id": github_id,
                "high_geo_count": "4",
                "mainstream_task_count": "4",
                "original_text_available": "Yes",
                "date_available": "Yes",
                "repeatable_discovery": "Yes",
            })
            write_rows(pilot_path, [row])

            pilot_run(run_dir)
            github = next(
                item for item in read_rows(pilot_path) if item["source_id"] == github_id
            )
            self.assertEqual(github["pilot_recommendation"], "Supplement")
            self.assertIn("technical", github["decision_reason"].lower())

    def test_auth_and_consent_boundaries_never_become_core(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            registry_path = run_dir / "02-source-discovery.csv"
            rows = read_rows(registry_path)
            for source_id, name, access in (
                ("SRC-ARE-login-only", "Login only source", "Auth-optional"),
                ("SRC-ARE-private-group", "Private group", "Consent-required"),
            ):
                row = {field: "" for field in rows[0]}
                row.update({
                    "source_id": source_id,
                    "country_iso3": "ARE",
                    "source_name": name,
                    "source_family": "local_forum",
                    "candidate_evidence_streams": "B",
                    "access_status": access,
                    "public_access": access,
                    "main_bias": "self_selection",
                })
                rows.append(row)
            write_rows(registry_path, rows)

            pilot_run(run_dir)
            by_id = {row["source_id"]: row for row in read_rows(run_dir / "03-channel-fit-pilot.csv")}
            self.assertEqual(by_id["SRC-ARE-login-only"]["pilot_recommendation"], "Auth-optional")
            self.assertEqual(by_id["SRC-ARE-private-group"]["pilot_recommendation"], "Consent-required")

    def test_human_approval_requires_signatures_and_core_or_gap_per_stream(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            self.seed_successful_trustpilot_pilot(run_dir)
            pilot_run(run_dir)
            plan_path = run_dir / "04-approved-source-plan.yml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan.update({
                "approval_status": "approved",
                "approved_by": "Gate A Reviewer",
                "approved_at": "2026-09-03T01:00:00+00:00",
                "approval_note": "Public anonymous path approved; B/C remain explicit pilot gaps.",
            })
            plan["streams"]["B"]["documented_gap"] = "No Core source after public pilot; use supplements and preserve the gap."
            plan["streams"]["C"]["documented_gap"] = "No Core source after public pilot; use supplements and preserve the gap."
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")

            result = pilot_run(run_dir)
            self.assertEqual(result["status"], "source_plan_approved")
            manifest = load_manifest(run_dir)
            self.assertEqual(manifest["state"], "source_plan_approved")
            self.assertEqual(manifest["approvals"]["source_plan"]["by"], "Gate A Reviewer")

    def test_approval_is_rejected_when_a_stream_has_neither_core_nor_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            self.seed_successful_trustpilot_pilot(run_dir)
            pilot_run(run_dir)
            plan_path = run_dir / "04-approved-source-plan.yml"
            plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
            plan.update({
                "approval_status": "approved",
                "approved_by": "Gate A Reviewer",
                "approved_at": "2026-09-03T01:00:00+00:00",
            })
            plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")

            with self.assertRaises(ManifestError):
                pilot_run(run_dir)
            self.assertEqual(load_manifest(run_dir)["state"], "source_plan_pending")


if __name__ == "__main__":
    unittest.main()
