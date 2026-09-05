import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from country_runner.manifest import (
    ManifestError,
    assert_run_writable,
    initialize_run,
    load_manifest,
    resolve_run_dir,
    transition_state,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_ROOT = PROJECT_ROOT / "country_runner"
LAUNCHER = PROJECT_ROOT / "country-runner"


class ManifestTests(unittest.TestCase):
    def init_run(self, runs_root: Path, run_id: str = "2026-09-03-demo") -> Path:
        return initialize_run(
            country_code="AE",
            run_id=run_id,
            runs_root=runs_root,
            config_root=RUNNER_ROOT / "config",
            templates_root=RUNNER_ROOT / "templates",
            researcher="Test Researcher",
        )

    def test_init_creates_complete_run_without_touching_real_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.init_run(Path(temp))
            expected = {
                "00-run-manifest.yml", "01-country-context.md", "02-source-discovery.csv",
                "03-channel-fit-pilot.csv", "04-approved-source-plan.yml", "queries",
                "evidence", "review", "output", "99-change-and-freeze-log.md",
            }
            self.assertEqual({path.name for path in run_dir.iterdir()}, expected)
            self.assertTrue((run_dir / "evidence" / "A-competitor-feedback.csv").exists())
            self.assertTrue((run_dir / "queries" / "A-competitor-queries.csv").exists())
            manifest = load_manifest(run_dir)
            self.assertEqual(manifest["state"], "initialized")
            self.assertEqual(manifest["country_iso3"], "ARE")
            self.assertTrue(manifest["input_hashes"]["country_config"])

    def test_init_refuses_to_overwrite_existing_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runs_root = Path(temp)
            self.init_run(runs_root)
            with self.assertRaises(ManifestError):
                self.init_run(runs_root)

    def test_state_machine_rejects_illegal_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.init_run(Path(temp))
            with self.assertRaises(ManifestError):
                transition_state(run_dir, "validation_pass")
            transition_state(run_dir, "discovery_ready")
            self.assertEqual(load_manifest(run_dir)["state"], "discovery_ready")

    def test_multiple_active_runs_require_explicit_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runs_root = Path(temp)
            first = self.init_run(runs_root, "run-one")
            self.init_run(runs_root, "run-two")
            with self.assertRaises(ManifestError):
                resolve_run_dir(runs_root, "AE")
            self.assertEqual(resolve_run_dir(runs_root, "AE", "run-one"), first)

    def test_frozen_run_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.init_run(Path(temp))
            manifest_path = run_dir / "00-run-manifest.yml"
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            manifest["state"] = "frozen"
            manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
            with self.assertRaises(ManifestError):
                assert_run_writable(run_dir)

    def test_cli_init_works_with_custom_runs_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [str(LAUNCHER), "init", "AE", "--run-id", "cli-demo", "--runs-root", temp],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(temp) / "AE" / "cli-demo" / "00-run-manifest.yml").exists())

    def test_init_accepts_run_specific_research_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = initialize_run(
                country_code="AE",
                run_id="window-demo",
                runs_root=Path(temp),
                config_root=RUNNER_ROOT / "config",
                templates_root=RUNNER_ROOT / "templates",
                researcher="Researcher",
                window_start="2026-01-01",
                window_end="2026-08-31",
            )
            manifest = load_manifest(run_dir)
            self.assertEqual(
                manifest["research_window"], {"start": "2026-01-01", "end": "2026-08-31"}
            )
            context = (run_dir / "01-country-context.md").read_text(encoding="utf-8")
            self.assertIn("2026-01-01", context)
            self.assertIn("2026-08-31", context)

    def test_init_rejects_invalid_research_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runs_root = Path(temp)
            with self.assertRaises(ManifestError):
                initialize_run(
                    country_code="AE",
                    run_id="bad-window",
                    runs_root=runs_root,
                    config_root=RUNNER_ROOT / "config",
                    templates_root=RUNNER_ROOT / "templates",
                    window_start="2026-09-01",
                    window_end="2026-08-31",
                )
            self.assertFalse((runs_root / "AE" / "bad-window").exists())


if __name__ == "__main__":
    unittest.main()
