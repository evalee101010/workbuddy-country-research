import csv
import tempfile
import unittest
from pathlib import Path

from country_runner.discovery import discover_run
from country_runner.manifest import initialize_run, load_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class DiscoveryTests(unittest.TestCase):
    def make_run(self, temp: str) -> Path:
        return initialize_run(
            country_code="AE",
            run_id="discovery-demo",
            runs_root=Path(temp),
            config_root=RUNNER_ROOT / "config",
            templates_root=RUNNER_ROOT / "templates",
            researcher="Researcher",
        )

    def test_discover_generates_source_registry_and_three_query_packs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            result = discover_run(run_dir, RUNNER_ROOT / "config")
            self.assertGreater(result["sources"], 0)
            self.assertEqual(load_manifest(run_dir)["state"], "discovery_ready")
            for name in (
                "A-competitor-queries.csv", "B-local-needs-queries.csv", "C-kol-koc-queries.csv"
            ):
                rows = read_rows(run_dir / "queries" / name)
                self.assertGreater(len(rows), 0, name)

    def test_uae_queries_cover_country_and_all_seven_emirates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            discover_run(run_dir, RUNNER_ROOT / "config")
            rows = read_rows(run_dir / "queries" / "B-local-needs-queries.csv")
            scopes = {row["scope_name"] for row in rows}
            self.assertIn("ARE", scopes)
            self.assertTrue({"Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"}.issubset(scopes))

    def test_language_roles_and_github_scope_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            discover_run(run_dir, RUNNER_ROOT / "config")
            all_rows = []
            for path in (run_dir / "queries").glob("*.csv"):
                all_rows.extend(read_rows(path))
            self.assertTrue({"core", "exploratory", "migration_corridor"}.issubset({row["language_role"] for row in all_rows}))
            github_rows = [row for row in all_rows if row["source_name"] == "GitHub"]
            self.assertTrue(github_rows)
            self.assertEqual({row["source_scope_default"] for row in github_rows}, {"global_technical"})

    def test_rerun_preserves_researcher_edits_in_source_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.make_run(temp)
            discover_run(run_dir, RUNNER_ROOT / "config")
            registry = run_dir / "02-source-discovery.csv"
            rows = read_rows(registry)
            rows[0]["researcher_note"] = "manual note must survive"
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            discover_run(run_dir, RUNNER_ROOT / "config")
            self.assertEqual(read_rows(registry)[0]["researcher_note"], "manual note must survive")


if __name__ == "__main__":
    unittest.main()
