import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import yaml

from .csvio import read_csv, read_header
from .manifest import ManifestError, load_manifest


def _table(path: Path) -> dict:
    headers = read_header(path)
    return {"headers": headers, "rows": [[row.get(field, "") for field in headers] for row in read_csv(path)]}


def _source_plan_rows(plan: dict) -> dict:
    headers = ["stream", "role", "source_id_or_gap"]
    rows = []
    for stream in ("A", "B", "C"):
        stream_plan = (plan.get("streams") or {}).get(stream, {})
        for key in ("core", "supplement", "discovery_only", "auth_optional", "consent_required"):
            for identifier in stream_plan.get(key) or []:
                rows.append([stream, key, identifier])
        if stream_plan.get("documented_gap"):
            rows.append([stream, "documented_gap", stream_plan["documented_gap"]])
    return {"headers": headers, "rows": rows}


def _citation_table(run_dir: Path) -> dict:
    headers = [
        "evidence_id", "content_id", "evidence_stream", "source_name", "original_text",
        "original_text_translation_cn", "country_confidence", "geo_evidence", "item_url",
    ]
    rows = []
    for stream, filename in (
        ("A", "A-competitor-feedback.csv"),
        ("B", "B-local-work-needs.csv"),
        ("C", "C-kol-koc-content.csv"),
    ):
        for row in read_csv(run_dir / "evidence" / filename):
            if row.get("inclusion_status") != "Included":
                continue
            rows.append([
                row.get("evidence_id", ""), row.get("content_id", ""), stream,
                row.get("source_name", ""), row.get("original_text", ""),
                row.get("original_text_translation_cn", ""), row.get("country_confidence", ""),
                row.get("geo_evidence", ""), row.get("item_url") or row.get("source_url", ""),
            ])
    return {"headers": headers, "rows": rows}


def _payload(run_dir: Path) -> Dict[str, object]:
    manifest = load_manifest(run_dir)
    plan = yaml.safe_load(
        (run_dir / "04-approved-source-plan.yml").read_text(encoding="utf-8")
    ) or {}
    validation_path = run_dir / "review" / "validation-result.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {}
    warning_rows = [
        [issue.get("severity", ""), issue.get("code", ""), issue.get("message", ""), issue.get("evidence_id", "")]
        for issue in validation.get("issues", [])
        if issue.get("severity") in {"WARN", "INFO"}
    ]
    return {
        "summary": {
            "country_iso2": manifest["country_iso2"],
            "country_iso3": manifest["country_iso3"],
            "run_id": manifest["run_id"],
            "validation_state": manifest["state"],
            "researcher": manifest.get("researcher", ""),
            "reviewer": manifest.get("reviewer", ""),
            "research_window": manifest.get("research_window", {}),
            "source_plan_approved_by": manifest.get("approvals", {}).get("source_plan", {}).get("by", ""),
            "evidence_audit_approved_by": manifest.get("approvals", {}).get("evidence_audit", {}).get("by", ""),
        },
        "tables": {
            "Source Plan": _source_plan_rows(plan),
            "Raw Discovery": _table(run_dir / "evidence" / "raw-discovery-log.csv"),
            "A": _table(run_dir / "evidence" / "A-competitor-feedback.csv"),
            "B": _table(run_dir / "evidence" / "B-local-work-needs.csv"),
            "C": _table(run_dir / "evidence" / "C-kol-koc-content.csv"),
            "Coverage": _table(run_dir / "review" / "coverage-matrix.csv"),
            "Audit": _table(run_dir / "review" / "evidence-audit.csv"),
            "Warnings": {
                "headers": ["severity", "code", "message", "evidence_id"],
                "rows": warning_rows,
            },
            "Citation Index": _citation_table(run_dir),
        },
    }


def build_xlsx(run_dir: Path, output_path: Path) -> None:
    run_dir = Path(run_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder = Path(__file__).resolve().parents[1] / "xlsx" / "build_country_workbook.mjs"
    if not builder.exists():
        raise ManifestError(f"XLSX builder not found: {builder}")
    node = os.environ.get("COUNTRY_RUNNER_NODE") or shutil.which("node")
    if not node:
        raise ManifestError("Node.js is required for the artifact-tool XLSX builder")
    input_path = output_path.with_name(f".{output_path.name}.input.json")
    inspection_path = output_path.with_name(f"{output_path.stem}-inspection.json")
    preview_dir = output_path.with_name(f"{output_path.stem}-previews")
    input_path.write_text(json.dumps(_payload(run_dir), ensure_ascii=False), encoding="utf-8")
    try:
        result = subprocess.run(
            [node, str(builder), str(input_path), str(output_path), str(preview_dir), str(inspection_path)],
            text=True,
            capture_output=True,
            check=False,
            env=os.environ.copy(),
        )
    finally:
        input_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise ManifestError(f"artifact-tool XLSX build failed: {result.stderr.strip() or result.stdout.strip()}")
    if not output_path.exists():
        raise ManifestError("artifact-tool completed without producing the XLSX output")
