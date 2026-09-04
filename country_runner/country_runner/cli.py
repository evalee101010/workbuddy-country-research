import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .paths import resolve_config_root, resolve_project_root, resolve_runs_root


CORE_COMMANDS = ("init", "discover", "pilot", "validate", "build")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="country-runner",
        description="公开需求信号国家研究 Runner",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--project-root", help=argparse.SUPPRESS)
    parser.add_argument("--runs-root", help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    help_text = {
        "init": "初始化单国 run 与模板",
        "discover": "生成本地渠道发现与多语言查询包",
        "pilot": "汇总渠道试跑并生成 Gate A 来源计划",
        "validate": "执行 Gate B 证据与覆盖校验",
        "build": "生成并冻结 Markdown/XLSX 国家包",
    }
    for command in CORE_COMMANDS:
        subparser = subparsers.add_parser(command, help=help_text[command])
        subparser.add_argument("country", metavar="COUNTRY", help="ISO2 国家代码")
        subparser.add_argument("--run-id")
        subparser.add_argument("--project-root")
        subparser.add_argument("--runs-root")

    return parser


def _path_payload(args: argparse.Namespace) -> dict:
    project_root = resolve_project_root(getattr(args, "project_root", None))
    return {
        "project_root": str(project_root),
        "config_root": str(resolve_config_root(project_root)),
        "runs_root": str(resolve_runs_root(project_root, getattr(args, "runs_root", None))),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_paths:
        print(json.dumps(_path_payload(args), ensure_ascii=False))
        return 0
    if not args.command:
        parser.print_help()
        return 0

    payload = _path_payload(args)
    payload.update({"command": args.command, "country": args.country.upper()})
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    print(f"{args.command} 尚未实现", file=sys.stderr)
    return 2
