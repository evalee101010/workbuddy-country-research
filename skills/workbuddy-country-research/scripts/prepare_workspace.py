#!/usr/bin/env python3
"""Install the bundled runner into a research workspace without touching the Skill."""

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path


RUNTIME_DIR = ".workbuddy-country-research"


def resolve_workspace(explicit=None):
    value = explicit or os.environ.get("WORKBUDDY_WORKSPACE_ROOT") or os.getcwd()
    return Path(value).expanduser().resolve()


def ensure_runtime(workspace):
    workspace = Path(workspace).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    if workspace == skill_root or skill_root in workspace.parents:
        raise RuntimeError("choose a research workspace outside the installed Skill directory")
    source = skill_root / "assets" / "country_runner"
    target_root = workspace / RUNTIME_DIR
    target = target_root / "country_runner"
    required = (
        target / "country_runner" / "__main__.py",
        target / "config" / "global" / "codebook.yml",
        target / "templates" / "raw-discovery-log.csv",
    )
    if target.exists():
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise RuntimeError("existing WorkBuddy runtime is incomplete: " + ", ".join(missing))
        return target, "reused"
    if not source.exists():
        raise RuntimeError(f"bundled runner is missing: {source}")
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="workbuddy-install-", dir=target_root) as temporary:
        staging = Path(temporary) / "country_runner"
        shutil.copytree(source, staging)
        staging.replace(target)
    return target, "prepared"


def main():
    parser = argparse.ArgumentParser(description="Prepare an isolated WorkBuddy country-research runtime.")
    parser.add_argument("--workspace")
    args = parser.parse_args()
    try:
        runtime, status = ensure_runtime(resolve_workspace(args.workspace))
    except (OSError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({"status": status, "runtime": str(runtime)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
