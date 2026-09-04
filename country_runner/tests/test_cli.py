import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = PROJECT_ROOT / "country-runner"


class CliSmokeTests(unittest.TestCase):
    def run_cli(
        self, *args: str, cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(LAUNCHER), *args],
            cwd=cwd or PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_lists_the_five_core_commands(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("init", "discover", "pilot", "validate", "build"):
            self.assertIn(command, result.stdout)

    def test_unknown_command_fails_clearly(self) -> None:
        result = self.run_cli("unknown-command")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_launcher_resolves_project_root_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as other_directory:
            result = self.run_cli("--show-paths", cwd=other_directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(Path(payload["project_root"]), PROJECT_ROOT)
        self.assertEqual(
            Path(payload["config_root"]), PROJECT_ROOT / "country_runner" / "config"
        )


if __name__ == "__main__":
    unittest.main()
