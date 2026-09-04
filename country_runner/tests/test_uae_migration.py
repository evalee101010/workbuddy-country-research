import hashlib
import tempfile
import unittest
from pathlib import Path

from country_runner.csvio import read_csv
from country_runner.manifest import initialize_run
from country_runner.migrate_uae import migrate_uae


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"
FIXTURE_ROOT = RUNNER_ROOT / "tests" / "fixtures" / "uae-legacy"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class UaeMigrationTests(unittest.TestCase):
    def make_run(self, temp: str) -> Path:
        return initialize_run(
            country_code="AE",
            run_id="migration-demo",
            runs_root=Path(temp),
            config_root=RUNNER_ROOT / "config",
            templates_root=RUNNER_ROOT / "templates",
            researcher="Researcher",
        )

    def test_migration_preserves_sources_and_reconciles_rows(self) -> None:
        before = {path.name: sha256(path) for path in FIXTURE_ROOT.glob("*.csv")}
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            result = migrate_uae(FIXTURE_ROOT, run_dir)
            raw = read_csv(run_dir / "evidence" / "raw-discovery-log.csv")
            evidence_a = read_csv(run_dir / "evidence" / "A-competitor-feedback.csv")
            evidence_c = read_csv(run_dir / "evidence" / "C-kol-koc-content.csv")

            self.assertEqual(result["source_rows"], {"raw_feedback": 1, "coded_feedback": 1, "kol_koc": 2})
            self.assertEqual(result["output_rows"], {"raw": 3, "A": 1, "C": 2})
            self.assertEqual(len(raw), 3)
            self.assertEqual(len(evidence_a), 1)
            self.assertEqual(len(evidence_c), 2)
        after = {path.name: sha256(path) for path in FIXTURE_ROOT.glob("*.csv")}
        self.assertEqual(before, after)

    def test_legacy_ids_quotes_and_translations_survive_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            migrate_uae(FIXTURE_ROOT, run_dir)
            raw = read_csv(run_dir / "evidence" / "raw-discovery-log.csv")
            by_legacy = {row["legacy_record_id"]: row for row in raw}
            feedback = by_legacy["FB-ARE-TEST-001"]
            self.assertEqual(feedback["original_text"], 'The output kept my quoted phrase, "ready to present".')
            self.assertEqual(feedback["original_text_translation_cn"], "输出保留了“可直接演示”的原话。")
            self.assertTrue(feedback["content_id"].startswith("CNT-"))

            coded = read_csv(run_dir / "evidence" / "A-competitor-feedback.csv")[0]
            self.assertEqual(coded["legacy_record_id"], "FB-ARE-TEST-001")
            self.assertEqual(coded["original_text"], feedback["original_text"])
            self.assertEqual(coded["content_id"], feedback["content_id"])
            self.assertTrue(coded["evidence_id"].startswith("EVD-"))

    def test_kol_mapping_keeps_emirate_confidence_and_does_not_infer_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            migrate_uae(FIXTURE_ROOT, run_dir)
            rows = read_csv(run_dir / "evidence" / "C-kol-koc-content.csv")
            abu_dhabi = next(row for row in rows if row["legacy_record_id"] == "MC-AE-TEST-001")
            self.assertEqual(abu_dhabi["admin1_name"], "Abu Dhabi")
            self.assertEqual(abu_dhabi["admin1_confidence"], "Medium")
            self.assertEqual(abu_dhabi["followers_visible"], "1200")
            self.assertEqual(abu_dhabi["clicks_visible"], "")
            self.assertEqual(abu_dhabi["audience_profile"], "")
            self.assertEqual(abu_dhabi["offer_price_original"], "")

    def test_duplicate_urls_are_only_reported_and_unmapped_fields_are_logged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            result = migrate_uae(FIXTURE_ROOT, run_dir)
            raw = read_csv(run_dir / "evidence" / "raw-discovery-log.csv")
            self.assertEqual(len(raw), 3)
            self.assertGreaterEqual(result["duplicate_hint_count"], 1)
            log = (run_dir / "review" / "legacy-uae-migration.md").read_text(encoding="utf-8")
            self.assertIn("Row reconciliation", log)
            self.assertIn("Unmapped legacy fields", log)
            self.assertIn("MC-AE-TEST-001", log)


if __name__ == "__main__":
    unittest.main()
