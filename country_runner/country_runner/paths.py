from pathlib import Path
from typing import Optional


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = PACKAGE_ROOT.parent


def resolve_project_root(value: Optional[str] = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return DEFAULT_PROJECT_ROOT


def resolve_config_root(project_root: Path) -> Path:
    return project_root / "country_runner" / "config"


def resolve_runs_root(project_root: Path, value: Optional[str] = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return project_root / "research" / "runs"
