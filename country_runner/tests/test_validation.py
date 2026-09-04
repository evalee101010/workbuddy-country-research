import tempfile
import unittest
from pathlib import Path

import yaml

from country_runner.config import load_country_config
from country_runner.csvio import read_csv, read_header, write_csv
from country_runner.discovery import discover_run
from country_runner.manifest import initialize_run, load_manifest, transition_state
from country_runner.validation import validate_run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"


class ValidationTests(unittest.TestCase):
    def make_ready_run(self, temp: str, mark_queries: bool = True) -> Path:
        run_dir = initialize_run(
            country_code="AE",
            run_id="validation-demo",
            runs_root=Path(temp),
            config_root=RUNNER_ROOT / "config",
            templates_root=RUNNER_ROOT / "templates",
            researcher="Researcher",
        )
        discover_run(run_dir, RUNNER_ROOT / "config")
        if mark_queries:
            for path in (run_dir / "queries").glob("*.csv"):
                rows = read_csv(path)
                for row in rows:
                    if row["language_role"] == "core":
                        row["status"] = "Completed"
                        row["results_inspected"] = "1"
                        row["valid_results"] = "1"
                write_csv(path, read_header(path), rows)

        registry_path = run_dir / "02-source-discovery.csv"
        registry = read_csv(registry_path)
        for identifier, name, family in (
            ("SRC-ARE-main", "Main Public Source", "review_platform"),
            ("SRC-ARE-second", "Second Public Source", "professional_social"),
        ):
            row = {field: "" for field in read_header(registry_path)}
            row.update({
                "source_id": identifier,
                "country_iso3": "ARE",
                "source_name": name,
                "source_url": f"https://example.com/{identifier}",
                "source_family": family,
                "local_role": "country_candidate",
                "candidate_evidence_streams": "A|B|C",
                "access_status": "Manual-Review",
                "public_access": "public_manual",
                "main_bias": "self_selection",
            })
            registry.append(row)
        write_csv(registry_path, read_header(registry_path), registry)

        plan_path = run_dir / "04-approved-source-plan.yml"
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan.update({
            "approval_status": "approved",
            "approved_by": "Gate A Reviewer",
            "approved_at": "2026-09-03T00:00:00+00:00",
            "anonymous_path_status": "ready",
            "source_decisions": [
                {"source_id": "SRC-ARE-main", "role": "Core", "streams": ["A", "B", "C"]},
                {"source_id": "SRC-ARE-second", "role": "Supplement", "streams": ["A", "B", "C"]},
            ],
        })
        for stream in ("A", "B", "C"):
            plan["streams"][stream]["core"] = ["SRC-ARE-main"]
            plan["streams"][stream]["supplement"] = ["SRC-ARE-second"]
        plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
        transition_state(run_dir, "source_plan_pending", "test")
        transition_state(run_dir, "source_plan_approved", "test")
        return run_dir

    def query_ids_by_task(self, run_dir: Path):
        output = {}
        for path in (run_dir / "queries").glob("*.csv"):
            for row in read_csv(path):
                if row["language_role"] == "core":
                    output.setdefault(row["task_family"], row["query_id"])
        return output

    def add_evidence(
        self,
        run_dir: Path,
        number: int,
        stream: str = "A",
        role: str = "office_workers",
        task: str = "office_productivity",
        source_id: str = "SRC-ARE-main",
        headline: bool = False,
        technical: str = "Non-technical",
        country_confidence: str = "High",
        geo_evidence: str = "Author public profile states United Arab Emirates.",
        original_text: str = "I used the tool to finish this work.",
        item_url: str = "",
        published_at: str = "2026-08-15",
    ) -> None:
        evidence_id = f"EVD-test-{number:03d}"
        content_id = f"CNT-test-{number:03d}"
        url = item_url if item_url != "" else f"https://example.com/items/{number}"
        query_id = self.query_ids_by_task(run_dir)[task]
        common = {
            "evidence_id": evidence_id,
            "content_id": content_id,
            "run_id": "validation-demo",
            "evidence_stream": stream,
            "source_id": source_id,
            "source_type": "Public page",
            "source_name": "Main Public Source" if source_id.endswith("main") else "Second Public Source",
            "source_url": "https://example.com",
            "item_url": url,
            "author_alias": f"Author {number}",
            "published_at": published_at,
            "published_at_raw": published_at,
            "date_confidence": "Exact",
            "captured_at": "2026-09-03",
            "query_id": query_id,
            "query_language": "en",
            "content_language": "en",
            "original_text": original_text,
            "original_text_translation_cn": "我使用该工具完成了工作。",
            "context_note": "Public post describing a concrete work task.",
            "country_iso3": "ARE",
            "country_or_region": "United Arab Emirates",
            "geo_evidence": geo_evidence,
            "country_confidence": country_confidence,
            "scope_level": "country",
            "scope_name": "ARE",
            "discovery_round": "country",
            "country_assignment_status": "exact_country",
            "audience_role": role,
            "technical_level": technical,
            "source_audience_bias": "self_selection",
            "inclusion_status": "Included",
            "review_status": "Pending",
            "headline_evidence": "Yes" if headline else "No",
            "normalized_theme": f"theme-{number}",
        }
        raw_path = run_dir / "evidence" / "raw-discovery-log.csv"
        raw = {field: "" for field in read_header(raw_path)}
        for field in raw:
            if field in common:
                raw[field] = common[field]
        raw["content_id"] = content_id
        raw["canonical_url"] = url
        raw_rows = read_csv(raw_path)
        raw_rows.append(raw)
        write_csv(raw_path, read_header(raw_path), raw_rows)

        filename = {
            "A": "A-competitor-feedback.csv",
            "B": "B-local-work-needs.csv",
            "C": "C-kol-koc-content.csv",
        }[stream]
        evidence_path = run_dir / "evidence" / filename
        row = {field: "" for field in read_header(evidence_path)}
        row.update({field: value for field, value in common.items() if field in row})
        if stream == "A":
            row.update({
                "product": "Genspark",
                "product_tier": "A1 Direct",
                "job_to_be_done": "Prepare a work deliverable",
                "actual_result": "Deliverable completed",
                "success_status": "Success",
            })
        elif stream == "B":
            row.update({
                "mainstream_fit": "Main-report",
                "work_task": "Prepare a work deliverable",
                "job_to_be_done": "Finish recurring office work",
                "pain_point": "Manual work takes too long",
                "desired_outcome": "A reviewed deliverable",
            })
        else:
            row.update({
                "creator_name": f"Creator {number}",
                "creator_type": "Practitioner",
                "content_format": "Video",
                "work_scene": task,
                "cta_type": "None",
            })
        rows = read_csv(evidence_path)
        rows.append(row)
        write_csv(evidence_path, read_header(evidence_path), rows)

    def sign_required_audit(self, run_dir: Path) -> None:
        path = run_dir / "review" / "evidence-audit.csv"
        rows = read_csv(path)
        for row in rows:
            if row["required_review"] == "Yes":
                row.update({
                    "review_status": "Reviewed-pass",
                    "reviewer": "Gate B Reviewer",
                    "reviewed_at": "2026-09-03T02:00:00+00:00",
                    "provenance_ok": "Yes",
                    "translation_ok": "Yes",
                    "geo_ok": "Yes",
                    "audience_ok": "Yes",
                    "dedup_ok": "Yes",
                    "issue_level": "PASS",
                })
        write_csv(path, read_header(path), rows)

    def seed_baseline_evidence(self, run_dir: Path) -> None:
        config = load_country_config(RUNNER_ROOT / "config", "AE")
        tasks = [task["id"] for task in config["task_families"]]
        roles = ["job_seekers", "office_workers", "sales_marketing"]
        for number in range(1, 11):
            self.add_evidence(
                run_dir,
                number,
                stream=("A", "B", "C")[(number - 1) % 3],
                role=roles[(number - 1) % len(roles)],
                task=tasks[(number - 1) % len(tasks)],
                source_id="SRC-ARE-main" if number % 2 else "SRC-ARE-second",
                headline=number <= 3,
            )

    def test_first_validate_seeds_audit_then_signed_review_can_warn_or_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp)
            self.seed_baseline_evidence(run_dir)
            first = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(first["status"], "validation_block")
            self.assertIn("reviewer_signature_missing", {issue["code"] for issue in first["issues"]})
            audit = read_csv(run_dir / "review" / "evidence-audit.csv")
            self.assertEqual(len(audit), 10)
            headline_rows = [row for row in audit if row["headline_evidence"] == "Yes"]
            self.assertEqual(len(headline_rows), 3)
            self.assertTrue(all(row["required_review"] == "Yes" for row in headline_rows))

            self.sign_required_audit(run_dir)
            second = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertIn(second["status"], {"validation_pass", "validation_warn"})
            manifest = load_manifest(run_dir)
            self.assertEqual(manifest["approvals"]["evidence_audit"]["status"], "approved")
            self.assertEqual(manifest["reviewer"], "Gate B Reviewer")

    def test_headline_missing_provenance_fields_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp)
            self.add_evidence(
                run_dir, 1, headline=True, original_text="", item_url=" ", published_at=""
            )
            result = validate_run(run_dir, RUNNER_ROOT / "config")
            codes = {issue["code"] for issue in result["issues"]}
            self.assertEqual(result["status"], "validation_block")
            self.assertTrue({"missing_original_text", "missing_item_url", "missing_published_at"}.issubset(codes))

    def test_low_geo_or_weak_geo_basis_cannot_support_country_headline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp)
            self.add_evidence(
                run_dir,
                1,
                headline=True,
                country_confidence="Low",
                geo_evidence="YouTube regionCode=AE and Arabic language only",
            )
            result = validate_run(run_dir, RUNNER_ROOT / "config")
            codes = {issue["code"] for issue in result["issues"]}
            self.assertIn("headline_low_geo_confidence", codes)
            self.assertIn("weak_geo_basis", codes)

    def test_developer_only_source_cannot_support_mainstream_headline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp)
            self.add_evidence(
                run_dir, 1, headline=True, role="developers", technical="Developer"
            )
            result = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertIn("developer_only_mainstream_claim", {issue["code"] for issue in result["issues"]})

    def test_attempted_but_sparse_public_evidence_warns_and_optional_metrics_do_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp)
            self.add_evidence(run_dir, 1, stream="A", role="office_workers", headline=True)
            self.add_evidence(run_dir, 2, stream="B", role="office_workers")
            self.add_evidence(run_dir, 3, stream="C", role="office_workers")
            validate_run(run_dir, RUNNER_ROOT / "config")
            self.sign_required_audit(run_dir)
            result = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(result["status"], "validation_warn")
            severities = {issue["code"]: issue["severity"] for issue in result["issues"]}
            self.assertEqual(severities["kol_optional_metrics_missing"], "INFO")
            self.assertEqual(severities["mainstream_role_coverage_low"], "WARN")

    def test_unattempted_mainstream_queries_block_even_if_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_ready_run(temp, mark_queries=False)
            self.add_evidence(run_dir, 1, headline=False)
            validate_run(run_dir, RUNNER_ROOT / "config")
            self.sign_required_audit(run_dir)
            result = validate_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(result["status"], "validation_block")
            self.assertIn("mainstream_queries_not_attempted", {issue["code"] for issue in result["issues"]})


if __name__ == "__main__":
    unittest.main()
