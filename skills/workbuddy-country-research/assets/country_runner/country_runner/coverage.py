from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml

from .csvio import read_csv, read_header, write_csv


QUERY_FILES = (
    "A-competitor-queries.csv",
    "B-local-needs-queries.csv",
    "C-kol-koc-queries.csv",
)


def _executed(row: dict) -> bool:
    status = str(row.get("status", "")).strip().lower()
    if status and status not in {"planned", "not-run", "not run"}:
        return True
    try:
        return int(row.get("results_inspected") or 0) > 0
    except ValueError:
        return False


def _issue(severity: str, code: str, message: str) -> dict:
    return {"severity": severity, "code": code, "message": message}


def _coverage_status(required: bool, attempted: bool, included: int) -> str:
    if required and not attempted:
        return "BLOCK"
    if included == 0:
        return "WARN"
    return "PASS"


def build_coverage(
    run_dir: Path,
    config: dict,
    evidence_rows: Iterable[dict],
) -> Tuple[List[dict], List[dict]]:
    run_dir = Path(run_dir)
    evidence = [row for row in evidence_rows if row.get("inclusion_status") == "Included"]
    queries = []
    for filename in QUERY_FILES:
        queries.extend(read_csv(run_dir / "queries" / filename))
    query_by_id = {row.get("query_id", ""): row for row in queries}
    executed = [row for row in queries if _executed(row)]
    executed_core = [row for row in executed if row.get("language_role") == "core"]

    required_roles = config["audiences"]["mainstream_roles"]
    required_tasks = [item["id"] for item in config["task_families"]]
    required_languages = config["languages"]["core"]
    attempted_roles = {row.get("audience_role") for row in executed_core}
    attempted_tasks = {row.get("task_family") for row in executed_core}
    attempted_languages = {row.get("query_language") for row in executed_core}

    nontechnical = [
        row for row in evidence
        if row.get("technical_level") not in {"Technical", "Developer"}
    ]
    role_counts = Counter(
        row.get("audience_role") for row in nontechnical
        if row.get("audience_role") in required_roles
    )
    task_counts = Counter()
    for row in nontechnical:
        task = query_by_id.get(row.get("query_id", ""), {}).get("task_family")
        if not task and row.get("normalized_theme") in required_tasks:
            task = row["normalized_theme"]
        if task in required_tasks:
            task_counts[task] += 1

    registry = {row["source_id"]: row for row in read_csv(run_dir / "02-source-discovery.csv")}
    source_families = {
        registry.get(row.get("source_id"), {}).get("source_family", "")
        for row in nontechnical
    } - {""}
    plan = yaml.safe_load(
        (run_dir / "04-approved-source-plan.yml").read_text(encoding="utf-8")
    ) or {}

    rows: List[dict] = []
    issues: List[dict] = []

    missing_roles = [role for role in required_roles if role not in attempted_roles]
    missing_tasks = [task for task in required_tasks if task not in attempted_tasks]
    missing_languages = [language for language in required_languages if language not in attempted_languages]
    if missing_roles or missing_tasks or missing_languages:
        pieces = []
        if missing_roles:
            pieces.append("roles=" + ",".join(missing_roles))
        if missing_tasks:
            pieces.append("tasks=" + ",".join(missing_tasks))
        if missing_languages:
            pieces.append("languages=" + ",".join(missing_languages))
        issues.append(_issue(
            "BLOCK",
            "mainstream_queries_not_attempted",
            "Required mainstream/core-language query categories were not attempted: " + "; ".join(pieces),
        ))

    for role in required_roles:
        attempted = role in attempted_roles
        count = role_counts[role]
        rows.append({
            "dimension": "mainstream_role",
            "category": role,
            "required": "Yes",
            "attempted": "Yes" if attempted else "No",
            "included_count": str(count),
            "source_family_count": "",
            "status": _coverage_status(True, attempted, count),
            "gap_note": "Attempted but no qualifying public evidence." if attempted and count == 0 else "",
        })
    for task in required_tasks:
        attempted = task in attempted_tasks
        count = task_counts[task]
        rows.append({
            "dimension": "task_family",
            "category": task,
            "required": "Yes",
            "attempted": "Yes" if attempted else "No",
            "included_count": str(count),
            "source_family_count": "",
            "status": _coverage_status(True, attempted, count),
            "gap_note": "Attempted but no qualifying public evidence." if attempted and count == 0 else "",
        })
    for language in required_languages:
        attempted = language in attempted_languages
        count = sum(1 for row in evidence if row.get("query_language") == language)
        rows.append({
            "dimension": "core_language",
            "category": language,
            "required": "Yes",
            "attempted": "Yes" if attempted else "No",
            "included_count": str(count),
            "source_family_count": "",
            "status": _coverage_status(True, attempted, count),
            "gap_note": "Queries were attempted but no qualifying evidence was included." if attempted and count == 0 else "",
        })

    role_baseline = int(config["research"]["required_mainstream_roles"])
    task_baseline = int(config["research"]["required_task_families"])
    family_baseline = int(config["research"]["required_source_families"])
    baseline_rows = (
        ("mainstream_role_baseline", role_baseline, len(role_counts)),
        ("task_family_baseline", task_baseline, len(task_counts)),
        ("source_family_baseline", family_baseline, len(source_families)),
    )
    for category, required, actual in baseline_rows:
        status = "PASS" if actual >= required else "WARN"
        rows.append({
            "dimension": "baseline",
            "category": category,
            "required": str(required),
            "attempted": "Yes" if executed_core else "No",
            "included_count": str(actual),
            "source_family_count": str(len(source_families)) if category == "source_family_baseline" else "",
            "status": status,
            "gap_note": "Public evidence remained below the configured baseline after queries." if status == "WARN" else "",
        })
    if len(role_counts) < role_baseline and not missing_roles:
        issues.append(_issue(
            "WARN", "mainstream_role_coverage_low",
            f"Queries were attempted, but qualifying evidence covers {len(role_counts)} of {role_baseline} required role families.",
        ))
    if len(task_counts) < task_baseline and not missing_tasks:
        issues.append(_issue(
            "WARN", "task_family_coverage_low",
            f"Queries were attempted, but qualifying evidence covers {len(task_counts)} of {task_baseline} required task families.",
        ))
    if len(source_families) < family_baseline:
        issues.append(_issue(
            "WARN", "source_family_coverage_low",
            f"Qualifying mainstream evidence uses {len(source_families)} of {family_baseline} required source families.",
        ))

    for stream in ("A", "B", "C"):
        stream_count = sum(1 for row in evidence if row.get("evidence_stream") == stream)
        stream_plan = (plan.get("streams") or {}).get(stream, {})
        core = stream_plan.get("core") or []
        gap = str(stream_plan.get("documented_gap", "")).strip()
        if stream_count:
            status, note = "PASS", ""
        elif gap:
            status, note = "WARN", gap
            issues.append(_issue("WARN", "stream_documented_gap", f"Stream {stream}: {gap}"))
        else:
            status, note = "BLOCK", "No Included evidence and no documented Gate A gap."
            issues.append(_issue(
                "BLOCK", "stream_missing_without_gap",
                f"Stream {stream} has no Included evidence and no documented gap.",
            ))
        rows.append({
            "dimension": "evidence_stream",
            "category": stream,
            "required": "Core or documented gap",
            "attempted": "Yes" if core or gap else "No",
            "included_count": str(stream_count),
            "source_family_count": str(len({
                registry.get(row.get("source_id"), {}).get("source_family", "")
                for row in evidence if row.get("evidence_stream") == stream
            } - {""})),
            "status": status,
            "gap_note": note,
        })

    admin1 = config["geography"].get("admin1", [])
    missing_admin1 = []
    for area in admin1:
        name = area["name_en"]
        count = sum(
            1 for row in evidence
            if row.get("admin1_name") == name and row.get("country_confidence") in {"High", "Medium"}
        )
        attempted = any(row.get("admin1_name") == name and _executed(row) for row in queries)
        if count == 0:
            missing_admin1.append(name)
        rows.append({
            "dimension": "subnational",
            "category": name,
            "required": "No",
            "attempted": "Yes" if attempted else "No",
            "included_count": str(count),
            "source_family_count": "",
            "status": "PASS" if count else "WARN",
            "gap_note": "No qualifying evidence; do not infer Dubai or another admin1." if count == 0 else "",
        })
    if missing_admin1:
        issues.append(_issue(
            "WARN", "subnational_gap",
            "No qualifying evidence for: " + ", ".join(missing_admin1),
        ))
    return rows, issues


def write_coverage(run_dir: Path, rows: Iterable[dict]) -> None:
    path = Path(run_dir) / "review" / "coverage-matrix.csv"
    write_csv(path, read_header(path), rows)
