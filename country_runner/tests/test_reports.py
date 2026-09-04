import tempfile
import unittest
from pathlib import Path

from country_runner.build import build_run
from country_runner.csvio import read_csv, read_header, write_csv
from country_runner.manifest import ManifestError, load_manifest, save_manifest, transition_state
from country_runner.report_md import render_markdown
from tests import test_validation as validation_helpers


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = validation_helpers.RUNNER_ROOT


class ReportTests(unittest.TestCase):
    def helper(self):
        return validation_helpers.ValidationTests()

    def test_markdown_always_has_eleven_sections_and_preserves_empty_streams(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.helper().make_ready_run(temp)
            report = render_markdown(run_dir, RUNNER_ROOT / "config")
            numbered = [line for line in report.splitlines() if line.startswith("## ")]
            self.assertEqual(len(numbered), 11)
            self.assertIn("## 4. A：竞品实际使用反馈", report)
            self.assertIn("本证据线暂无合格 Included 记录", report)
            self.assertIn("已执行查询", report)

    def test_report_citations_trace_to_content_original_and_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.helper().make_ready_run(temp)
            self.helper().add_evidence(run_dir, 1, stream="A", headline=True)
            report = render_markdown(run_dir, RUNNER_ROOT / "config")
            self.assertIn("EVD-test-001", report)
            self.assertIn("CNT-test-001", report)
            self.assertIn("I used the tool to finish this work.", report)
            self.assertIn("https://example.com/items/1", report)

    def test_developer_evidence_is_kept_out_of_mainstream_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.helper().make_ready_run(temp)
            self.helper().add_evidence(
                run_dir, 1, stream="A", role="developers", technical="Developer"
            )
            report = render_markdown(run_dir, RUNNER_ROOT / "config")
            mainstream = report.split("## 7. 主流非开发者人群", 1)[1].split("## 8.", 1)[0]
            technical = report.split("## 9. 技术补充", 1)[1].split("## 10.", 1)[0]
            self.assertNotIn("EVD-test-001", mainstream)
            self.assertIn("EVD-test-001", technical)

    def test_kol_metrics_are_listed_per_item_and_unknown_clicks_stay_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.helper().make_ready_run(temp)
            self.helper().add_evidence(run_dir, 1, stream="C")
            c_path = run_dir / "evidence" / "C-kol-koc-content.csv"
            rows = read_csv(c_path)
            rows[0]["views_visible"] = "1200"
            rows[0]["likes_visible"] = "75"
            write_csv(c_path, read_header(c_path), rows)
            report = render_markdown(run_dir, RUNNER_ROOT / "config")
            c_section = report.split("## 6. C：KOL/KOC 内容与商业承接", 1)[1].split("## 7.", 1)[0]
            self.assertIn("views=1200", c_section)
            self.assertIn("likes=75", c_section)
            self.assertIn("clicks=Unknown", c_section)
            self.assertNotIn("总播放", c_section)

    def test_build_requires_gate_b_signature_then_freezes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.helper().make_ready_run(temp)
            with self.assertRaises(ManifestError):
                build_run(run_dir, RUNNER_ROOT / "config", xlsx_builder=lambda *_: None)

            transition_state(run_dir, "collection_in_progress", "test")
            transition_state(run_dir, "validation_warn", "test")
            manifest = load_manifest(run_dir)
            manifest["reviewer"] = "Gate B Reviewer"
            manifest["approvals"]["source_plan"] = {
                "status": "approved", "by": "Gate A Reviewer", "at": "2026-09-03"
            }
            manifest["approvals"]["evidence_audit"] = {
                "status": "approved", "by": "Gate B Reviewer", "at": "2026-09-03"
            }
            save_manifest(run_dir, manifest)

            def fake_xlsx(_run_dir, output_path):
                Path(output_path).write_bytes(b"fake xlsx")

            result = build_run(run_dir, RUNNER_ROOT / "config", xlsx_builder=fake_xlsx)
            self.assertEqual(result["status"], "frozen")
            self.assertTrue((run_dir / "output" / "country-feedback-pack.md").exists())
            self.assertTrue((run_dir / "output" / "country-feedback-pack.xlsx").exists())
            self.assertEqual(load_manifest(run_dir)["state"], "frozen")
            with self.assertRaises(ManifestError):
                build_run(run_dir, RUNNER_ROOT / "config", xlsx_builder=fake_xlsx)

    def test_unique_artifact_tool_builder_declares_required_sheets(self) -> None:
        builder = PROJECT_ROOT / "country_runner" / "xlsx" / "build_country_workbook.mjs"
        text = builder.read_text(encoding="utf-8")
        self.assertIn('@oai/artifact-tool', text)
        self.assertNotIn('=HYPERLINK(', text)
        for sheet in (
            "Summary", "Source Plan", "Raw Discovery", "A", "B", "C",
            "Coverage", "Audit", "Warnings", "Citation Index",
        ):
            self.assertIn(f'"{sheet}"', text)


if __name__ == "__main__":
    unittest.main()
