import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .data_package import package_country_run
from .internal_validation import validate_internal_run
from .manifest import ManifestError, resolve_run_dir
from .merge_packages import merge_country_packages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workbuddy-internal-data",
        description="Validate, package and merge internal WorkBuddy country research data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "package"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("country")
        subparser.add_argument("--run-id", required=True)
        subparser.add_argument("--runs-root", required=True)
        subparser.add_argument("--config-root", required=True)
        subparser.add_argument("--templates-root", required=True)
        if command == "package":
            subparser.add_argument("--output-dir", required=True)

    merge = subparsers.add_parser("merge")
    merge.add_argument("packages", nargs="+")
    merge.add_argument("--output-dir", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command in {"validate", "package"}:
            run_dir = resolve_run_dir(Path(args.runs_root), args.country, args.run_id)
            if args.command == "validate":
                result = validate_internal_run(
                    run_dir, Path(args.config_root), Path(args.templates_root)
                )
            else:
                result = package_country_run(
                    run_dir,
                    Path(args.config_root),
                    Path(args.templates_root),
                    Path(args.output_dir),
                )
        else:
            result = merge_country_packages(
                [Path(path) for path in args.packages], Path(args.output_dir)
            )
    except (ManifestError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
