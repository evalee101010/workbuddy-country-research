import csv
import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"


def csv_header(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


class TemplateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = yaml.safe_load(
            (RUNNER_ROOT / "schemas" / "table-fields.yml").read_text(encoding="utf-8")
        )

    def test_every_csv_header_matches_the_machine_readable_schema(self) -> None:
        for filename, fields in self.schema["tables"].items():
            with self.subTest(filename=filename):
                header = csv_header(RUNNER_ROOT / "templates" / filename)
                self.assertEqual(header, fields)
                self.assertEqual(len(header), len(set(header)), "duplicate fields")

    def test_raw_and_coded_id_layers_are_separate(self) -> None:
        raw = self.schema["tables"]["raw-discovery-log.csv"]
        self.assertIn("content_id", raw)
        self.assertNotIn("evidence_id", raw)
        for filename in (
            "A-competitor-feedback.csv",
            "B-local-work-needs.csv",
            "C-kol-koc-content.csv",
        ):
            fields = self.schema["tables"][filename]
            self.assertIn("content_id", fields)
            self.assertIn("evidence_id", fields)

    def test_c_template_keeps_platform_metrics_separate(self) -> None:
        fields = self.schema["tables"]["C-kol-koc-content.csv"]
        for field in (
            "views_visible", "likes_visible", "comments_visible", "shares_visible",
            "clicks_visible", "followers_visible", "metric_captured_at",
        ):
            self.assertIn(field, fields)

    def test_common_enums_include_audience_scope_and_channel_roles(self) -> None:
        codebook = yaml.safe_load(
            (RUNNER_ROOT / "config" / "global" / "codebook.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            codebook["technical_level"],
            ["Non-technical", "No-code-capable", "Technical", "Developer", "Unknown"],
        )
        self.assertIn("migration_corridor", codebook["scope_level"])
        self.assertIn("global_unknown", codebook["scope_level"])
        self.assertEqual(
            codebook["channel_role"],
            ["Core", "Supplement", "Discovery-only", "Auth-optional", "Consent-required", "Reject"],
        )

    def test_developer_products_remain_reference_tier(self) -> None:
        products = yaml.safe_load(
            (RUNNER_ROOT / "config" / "global" / "product-catalog.yml").read_text(encoding="utf-8")
        )
        self.assertIn("Claude Code", products["tiers"]["D_reference"])
        self.assertIn("GitHub Copilot", products["tiers"]["D_reference"])


if __name__ == "__main__":
    unittest.main()
