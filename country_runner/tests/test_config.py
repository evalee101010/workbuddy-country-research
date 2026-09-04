import unittest
from pathlib import Path

from country_runner.config import ConfigError, load_all_country_configs, load_country_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = PROJECT_ROOT / "country_runner" / "config"
EXPECTED_CODES = {"AE", "SA", "US", "GB", "DE", "JP", "SG", "ID", "IN", "BR"}


class CountryConfigTests(unittest.TestCase):
    def test_all_ten_seed_configs_load(self) -> None:
        configs = load_all_country_configs(CONFIG_ROOT)
        self.assertEqual(set(configs), EXPECTED_CODES)
        self.assertEqual({item["identity"]["iso3"] for item in configs.values()}, {
            "ARE", "SAU", "USA", "GBR", "DEU", "JPN", "SGP", "IDN", "IND", "BRA"
        })

    def test_every_country_has_required_research_groups(self) -> None:
        for code, config in load_all_country_configs(CONFIG_ROOT).items():
            with self.subTest(country=code):
                for key in (
                    "identity", "languages", "geography", "audiences", "task_families",
                    "products", "channels", "access", "research", "regional_mappings",
                ):
                    self.assertIn(key, config)
                self.assertTrue(config["access"]["anonymous_public_path"])
                self.assertGreaterEqual(len(config["audiences"]["mainstream_roles"]), 3)
                self.assertGreaterEqual(len(config["task_families"]), 4)
                self.assertTrue(config["languages"]["core"])

    def test_platform_seeds_are_candidates_not_preapproved_sources(self) -> None:
        for code, config in load_all_country_configs(CONFIG_ROOT).items():
            for channel in config["channels"]:
                with self.subTest(country=code, channel=channel["name"]):
                    self.assertEqual(channel["status"], "Candidate")
                    self.assertIn(channel["scope_default"], {
                        "country_candidate", "global_technical", "global_unknown",
                        "migration_corridor", "recruitment_only",
                    })

    def test_uae_has_all_emirates_and_unknown_fallback(self) -> None:
        config = load_country_config(CONFIG_ROOT, "AE")
        admin1 = config["geography"]["admin1"]
        codes = {item["code"] for item in admin1}
        self.assertEqual(codes, {"AE-AZ", "AE-DU", "AE-SH", "AE-AJ", "AE-UQ", "AE-RK", "AE-FU"})
        self.assertTrue(config["geography"]["allow_unknown_admin1"])

    def test_saudi_and_uae_keep_separate_geo_and_language_rules(self) -> None:
        ae = load_country_config(CONFIG_ROOT, "AE")
        sa = load_country_config(CONFIG_ROOT, "SA")
        self.assertNotEqual(ae["geography"]["country_anchors"], sa["geography"]["country_anchors"])
        self.assertNotEqual(ae["geography"]["admin1"], sa["geography"]["admin1"])
        self.assertIn("ar", ae["languages"]["core"])
        self.assertIn("ar", sa["languages"]["core"])

    def test_github_is_never_a_country_native_seed(self) -> None:
        for code, config in load_all_country_configs(CONFIG_ROOT).items():
            github = [channel for channel in config["channels"] if channel["name"] == "GitHub"]
            self.assertEqual(len(github), 1, code)
            self.assertEqual(github[0]["scope_default"], "global_technical")
            self.assertEqual(github[0]["audience_bias"], "Developer")

    def test_unknown_top_level_fields_are_rejected(self) -> None:
        config = load_country_config(CONFIG_ROOT, "AE")
        config["typo_field"] = True
        with self.assertRaises(ConfigError):
            from country_runner.config import validate_country_config
            validate_country_config(config, expected_iso2="AE")


if __name__ == "__main__":
    unittest.main()
