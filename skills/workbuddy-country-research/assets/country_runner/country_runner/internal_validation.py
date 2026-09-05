import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlsplit

import yaml

from .config import load_country_config
from .manifest import ManifestError, load_manifest, utc_now


CSV_TABLES = {
    "02-source-discovery.csv": ("source-discovery.csv", "source_id"),
    "03-channel-fit-pilot.csv": ("channel-fit-pilot.csv", "source_id"),
    "evidence/raw-discovery-log.csv": ("raw-discovery-log.csv", "content_id"),
    "evidence/A-competitor-feedback.csv": ("A-competitor-feedback.csv", "evidence_id"),
    "evidence/B-local-work-needs.csv": ("B-local-work-needs.csv", "evidence_id"),
    "evidence/C-kol-koc-content.csv": ("C-kol-koc-content.csv", "evidence_id"),
    "queries/A-competitor-queries.csv": ("A-competitor-queries.csv", "query_id"),
    "queries/B-local-needs-queries.csv": ("B-local-needs-queries.csv", "query_id"),
    "queries/C-kol-koc-queries.csv": ("C-kol-koc-queries.csv", "query_id"),
}

EVIDENCE_PATHS = {
    "A": "evidence/A-competitor-feedback.csv",
    "B": "evidence/B-local-work-needs.csv",
    "C": "evidence/C-kol-koc-content.csv",
}

QUERY_PATHS = {
    "A": "queries/A-competitor-queries.csv",
    "B": "queries/B-local-needs-queries.csv",
    "C": "queries/C-kol-koc-queries.csv",
}

REQUIRED_NON_CSV = (
    "00-run-manifest.yml",
    "01-country-context.md",
    "04-approved-source-plan.yml",
)

PENDING_STATUSES = {"", "planned", "not-run", "not run"}
ALLOWED_INCLUDED_ROLES = {"Core", "Supplement", "Auth-optional"}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


def _read_csv(path: Path) -> List[dict]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _header(path: Path) -> List[str]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def _write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _issue(severity: str, code: str, message: str, record_id: str = "", path: str = "") -> dict:
    output = {"severity": severity, "code": code, "message": message}
    if record_id:
        output["record_id"] = record_id
    if path:
        output["path"] = path
    return output


def _valid_url(value: str) -> bool:
    try:
        parsed = urlsplit(str(value or "").strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _integer(value: object) -> int:
    return int(str(value or "0").strip())


def _split(value: object) -> List[str]:
    return [part.strip() for part in str(value or "").replace(",", "|").split("|") if part.strip()]


def _executed(row: dict) -> bool:
    status = str(row.get("status", "")).strip().lower()
    if status not in PENDING_STATUSES:
        return True
    try:
        return _integer(row.get("results_inspected")) > 0
    except ValueError:
        return False


def _plan_path(run_dir: Path) -> Path:
    preferred = Path(run_dir) / "04-approved-source-plan.yml"
    alternate = Path(run_dir) / "04-source-plan.yml"
    if preferred.exists():
        return preferred
    if alternate.exists():
        return alternate
    return preferred


def _load_plan(run_dir: Path) -> dict:
    path = _plan_path(run_dir)
    if not path.exists():
        raise ManifestError(f"source plan not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ManifestError(f"invalid source plan: {path}")
    return payload


def _dedupe_issues(issues: Iterable[dict]) -> List[dict]:
    output: List[dict] = []
    seen = set()
    for issue in issues:
        key = tuple((key, str(value)) for key, value in sorted(issue.items()))
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def _schema_issues(run_dir: Path, templates_root: Path) -> Tuple[List[dict], Dict[str, List[dict]]]:
    issues: List[dict] = []
    tables: Dict[str, List[dict]] = {}
    for relative, (template_name, id_field) in CSV_TABLES.items():
        path = Path(run_dir) / relative
        template = Path(templates_root) / template_name
        if not path.exists():
            issues.append(_issue("BLOCK", "required_file_missing", "Required table is missing.", path=relative))
            continue
        if not template.exists():
            raise ManifestError(f"template not found: {template}")
        actual_header = _header(path)
        expected_header = _header(template)
        if actual_header != expected_header:
            issues.append(_issue(
                "BLOCK", "schema_mismatch",
                "CSV header does not match the bundled schema.", path=relative,
            ))
        rows = _read_csv(path)
        tables[relative] = rows
        values = [str(row.get(id_field, "")).strip() for row in rows]
        if any(not value for value in values):
            issues.append(_issue("BLOCK", "blank_primary_id", f"Blank {id_field} found.", path=relative))
        duplicates = sorted(value for value, count in Counter(values).items() if value and count > 1)
        for duplicate in duplicates:
            issues.append(_issue(
                "BLOCK", "duplicate_primary_id", f"Duplicate {id_field}: {duplicate}",
                record_id=duplicate, path=relative,
            ))
    for id_field, relatives in (
        ("query_id", tuple(QUERY_PATHS.values())),
        ("evidence_id", tuple(EVIDENCE_PATHS.values())),
    ):
        occurrences = Counter(
            str(row.get(id_field, "")).strip()
            for relative in relatives
            for row in tables.get(relative, [])
            if str(row.get(id_field, "")).strip()
        )
        for duplicate in sorted(value for value, count in occurrences.items() if count > 1):
            issues.append(_issue(
                "BLOCK", "duplicate_primary_id_across_streams",
                f"Duplicate {id_field} across A/B/C tables: {duplicate}", record_id=duplicate,
            ))
    return issues, tables


def _query_issues(config: dict, tables: Dict[str, List[dict]]) -> Tuple[List[dict], set]:
    issues: List[dict] = []
    all_rows: List[dict] = []
    for stream, path in QUERY_PATHS.items():
        for row in tables.get(path, []):
            row = dict(row)
            row["_stream"] = stream
            all_rows.append(row)
            identifier = row.get("query_id", "")
            if row.get("evidence_stream") != stream:
                issues.append(_issue(
                    "BLOCK", "query_stream_mismatch",
                    f"Query row in stream {stream} table declares {row.get('evidence_stream') or 'blank'}.",
                    record_id=identifier, path=path,
                ))
            try:
                inspected = _integer(row.get("results_inspected"))
                valid = _integer(row.get("valid_results"))
                if inspected < 0 or valid < 0 or valid > inspected:
                    raise ValueError
            except ValueError:
                issues.append(_issue(
                    "BLOCK", "invalid_query_counts",
                    "results_inspected and valid_results must be non-negative integers with valid_results <= results_inspected.",
                    record_id=identifier, path=path,
                ))
            if row.get("language_role") == "core" and not _executed(row):
                issues.append(_issue(
                    "BLOCK", "core_query_not_executed",
                    "Core-language query remains Planned/Not-run.", record_id=identifier, path=path,
                ))

    executed_core = [row for row in all_rows if row.get("language_role") == "core" and _executed(row)]
    attempted_roles = {row.get("audience_role") for row in executed_core}
    attempted_tasks = {row.get("task_family") for row in executed_core}
    attempted_languages = {
        language for row in executed_core for language in _split(row.get("query_language"))
    }
    missing_roles = set(config["audiences"]["mainstream_roles"]) - attempted_roles
    missing_tasks = {item["id"] for item in config["task_families"]} - attempted_tasks
    missing_languages = set(config["languages"]["core"]) - attempted_languages
    for code, missing in (
        ("mainstream_role_queries_missing", missing_roles),
        ("task_family_queries_missing", missing_tasks),
        ("core_language_queries_missing", missing_languages),
    ):
        if missing:
            issues.append(_issue("BLOCK", code, "Required query coverage is missing: " + ", ".join(sorted(missing))))
    execution_text = " ".join(
        f"{row.get('status', '')} {row.get('notes', '')}".lower().replace("-", "_")
        for row in all_rows
    )
    saturated = "saturation_batch_1" in execution_text and "saturation_batch_2" in execution_text
    limited = any(
        label in execution_text for label in ("ranking_limited", "access_limited", "budget_limited")
    )
    if not saturated and not limited:
        issues.append(_issue(
            "BLOCK", "collection_stop_basis_missing",
            "Record two zero-new saturation batches or an explicit ranking/access/budget limit in query status/notes.",
        ))
    return issues, {row.get("query_id", "") for row in all_rows if row.get("query_id")}


def _source_and_plan_issues(plan: dict, tables: Dict[str, List[dict]]) -> Tuple[List[dict], set, Dict[str, str]]:
    issues: List[dict] = []
    registry = tables.get("02-source-discovery.csv", [])
    source_ids = {row.get("source_id", "") for row in registry if row.get("source_id")}
    decision_rows = [row for row in plan.get("source_decisions", []) if row.get("source_id")]
    decision_counts = Counter(row.get("source_id", "") for row in decision_rows)
    for duplicate in sorted(identifier for identifier, count in decision_counts.items() if count > 1):
        issues.append(_issue(
            "BLOCK", "duplicate_source_plan_decision",
            "Source has more than one role decision.", record_id=duplicate,
        ))
    decisions = {row.get("source_id", ""): row.get("role", "") for row in decision_rows}
    for identifier in decisions:
        if identifier not in source_ids:
            issues.append(_issue(
                "BLOCK", "plan_source_missing_from_registry",
                "Source plan references a source absent from source discovery.", record_id=identifier,
            ))
    for identifier, role in decisions.items():
        if role not in {
            "Core", "Supplement", "Discovery-only", "Auth-optional",
            "Consent-required", "Reject",
        }:
            issues.append(_issue(
                "BLOCK", "invalid_source_role", f"Unknown source role: {role}", record_id=identifier,
            ))
    for stream in ("A", "B", "C"):
        stream_plan = (plan.get("streams") or {}).get(stream, {})
        if not stream_plan.get("core") and not str(stream_plan.get("documented_gap", "")).strip():
            issues.append(_issue(
                "BLOCK", "stream_without_core_or_gap",
                f"Stream {stream} needs at least one Core source or a documented_gap.",
            ))
        for role_key, expected_role in (("core", "Core"), ("supplement", "Supplement")):
            for identifier in stream_plan.get(role_key, []) or []:
                if identifier not in source_ids:
                    issues.append(_issue(
                        "BLOCK", "stream_plan_source_missing",
                        f"Stream {stream} {role_key} source is absent from discovery.", identifier,
                    ))
                elif decisions.get(identifier) != expected_role:
                    issues.append(_issue(
                        "BLOCK", "stream_plan_role_mismatch",
                        f"Stream {stream} lists source as {expected_role} but its decision is {decisions.get(identifier) or 'missing'}.",
                        identifier,
                    ))
    return issues, source_ids, decisions


def _evidence_issues(
    manifest: dict,
    tables: Dict[str, List[dict]],
    source_ids: set,
    source_roles: Dict[str, str],
    query_ids: set,
) -> Tuple[List[dict], List[dict], List[dict]]:
    issues: List[dict] = []
    raw_rows = tables.get("evidence/raw-discovery-log.csv", [])
    raw_by_id = {row.get("content_id", ""): row for row in raw_rows if row.get("content_id")}
    canonical_counts = Counter(
        row.get("canonical_url", "").strip() for row in raw_rows if row.get("canonical_url", "").strip()
    )
    for url, count in canonical_counts.items():
        if count > 1:
            issues.append(_issue("BLOCK", "duplicate_canonical_url", f"Raw canonical URL appears {count} times: {url}"))

    for row in raw_rows:
        identifier = row.get("content_id", "")
        if row.get("source_id") and row.get("source_id") not in source_ids:
            issues.append(_issue("BLOCK", "raw_source_missing", "Raw row source is absent from source discovery.", identifier))
        for query_id in _split(row.get("query_hit_ids")):
            if query_id not in query_ids:
                issues.append(_issue("BLOCK", "raw_query_missing", f"Raw row references unknown query: {query_id}", identifier))
        if row.get("inclusion_status") == "Included":
            for field in (
                "run_id", "source_id", "item_url", "canonical_url", "query_hit_ids",
                "content_language", "original_text", "country_iso3", "geo_evidence",
                "country_confidence", "country_assignment_status",
            ):
                if not str(row.get(field, "")).strip():
                    issues.append(_issue(
                        "BLOCK", f"included_raw_missing_{field}",
                        f"Included raw row lacks {field}.", identifier, "evidence/raw-discovery-log.csv",
                    ))
            if row.get("item_url") and not _valid_url(row["item_url"]):
                issues.append(_issue("BLOCK", "invalid_raw_item_url", "Raw item_url is not a valid HTTP(S) URL.", identifier))
            if row.get("canonical_url") and not _valid_url(row["canonical_url"]):
                issues.append(_issue("BLOCK", "invalid_raw_canonical_url", "Raw canonical_url is not a valid HTTP(S) URL.", identifier))
            if row.get("run_id") != manifest.get("run_id"):
                issues.append(_issue("BLOCK", "raw_run_mismatch", "Raw run_id differs from manifest.", identifier))
            if row.get("country_iso3") != manifest.get("country_iso3"):
                issues.append(_issue("BLOCK", "raw_country_mismatch", "Raw country_iso3 differs from manifest.", identifier))
            if row.get("country_confidence") not in {"High", "Medium"}:
                issues.append(_issue(
                    "BLOCK", "raw_country_confidence_too_low",
                    "Included raw country_confidence must be High or Medium.", identifier,
                ))
            if row.get("country_assignment_status") not in {"exact_country", "multi_country"}:
                issues.append(_issue(
                    "BLOCK", "raw_country_assignment_unresolved",
                    "Included raw must have exact_country or multi_country assignment.", identifier,
                ))
            role = source_roles.get(row.get("source_id"), "")
            if not role:
                issues.append(_issue(
                    "BLOCK", "raw_source_role_decision_missing",
                    "Included raw source has no recorded role decision.", identifier,
                ))
            elif role not in ALLOWED_INCLUDED_ROLES:
                issues.append(_issue(
                    "BLOCK", "raw_source_role_not_eligible",
                    f"Included raw row uses source role {role}.", identifier,
                ))
            elif role == "Auth-optional" and not str(row.get("capture_mode", "")).lower().startswith("authorized"):
                issues.append(_issue(
                    "BLOCK", "auth_source_without_authorized_capture",
                    "Auth-optional raw evidence must record an authorized capture_mode.", identifier,
                ))
            if not str(row.get("published_at", "")).strip():
                issues.append(_issue(
                    "WARN", "raw_publication_date_missing",
                    "Included raw has no visible publication date.", identifier,
                ))
        text = " ".join(str(row.get(field, "")) for field in ("original_text", "context_note"))
        if EMAIL_RE.search(text) or PHONE_RE.search(text):
            issues.append(_issue(
                "WARN", "possible_personal_contact_detail",
                "Raw excerpt may contain an email address or phone number; verify that personal contact details were removed.", identifier,
            ))

    all_evidence: List[dict] = []
    included: List[dict] = []
    required_fields = (
        "content_id", "source_id", "item_url", "original_text", "geo_evidence",
        "country_confidence", "country_assignment_status",
    )
    for stream, path in EVIDENCE_PATHS.items():
        for row in tables.get(path, []):
            row = dict(row)
            row["evidence_stream"] = row.get("evidence_stream") or stream
            all_evidence.append(row)
            if row.get("inclusion_status") != "Included":
                continue
            included.append(row)
            identifier = row.get("evidence_id", "")
            for field in required_fields:
                if not str(row.get(field, "")).strip():
                    issues.append(_issue("BLOCK", f"included_evidence_missing_{field}", f"Included evidence lacks {field}.", identifier, path))
            if row.get("content_id") not in raw_by_id:
                issues.append(_issue("BLOCK", "raw_provenance_missing", "Evidence does not link to a raw row.", identifier, path))
            elif raw_by_id[row["content_id"]].get("inclusion_status") != "Included":
                issues.append(_issue("BLOCK", "raw_not_included", "Included evidence links to a non-Included raw row.", identifier, path))
            else:
                raw = raw_by_id[row["content_id"]]
                if row.get("source_id") != raw.get("source_id"):
                    issues.append(_issue("BLOCK", "raw_source_mismatch", "Evidence source_id differs from linked raw.", identifier, path))
                if row.get("item_url") != raw.get("item_url"):
                    issues.append(_issue("BLOCK", "raw_url_mismatch", "Evidence item_url differs from linked raw.", identifier, path))
                if row.get("query_id") not in _split(raw.get("query_hit_ids")):
                    issues.append(_issue("BLOCK", "raw_query_link_missing", "Evidence query_id is absent from raw query_hit_ids.", identifier, path))
            if row.get("source_id") not in source_ids:
                issues.append(_issue("BLOCK", "evidence_source_missing", "Evidence source is absent from source discovery.", identifier, path))
            role = source_roles.get(row.get("source_id"), "")
            if not role:
                issues.append(_issue(
                    "BLOCK", "source_role_decision_missing",
                    "Included evidence source has no recorded role decision in the source plan.", identifier, path,
                ))
            elif role not in ALLOWED_INCLUDED_ROLES:
                issues.append(_issue("BLOCK", "source_role_not_evidence_eligible", f"Included evidence uses source role {role}.", identifier, path))
            if row.get("evidence_stream") != stream:
                issues.append(_issue(
                    "BLOCK", "evidence_stream_mismatch",
                    f"Evidence row in stream {stream} table declares {row.get('evidence_stream') or 'blank'}.",
                    identifier, path,
                ))
            if row.get("query_id") not in query_ids:
                issues.append(_issue("BLOCK", "evidence_query_missing", "Evidence references an unknown query.", identifier, path))
            if row.get("item_url") and not _valid_url(row["item_url"]):
                issues.append(_issue("BLOCK", "invalid_item_url", "item_url is not a valid HTTP(S) URL.", identifier, path))
            if row.get("run_id") != manifest.get("run_id"):
                issues.append(_issue("BLOCK", "evidence_run_mismatch", "Evidence run_id differs from manifest.", identifier, path))
            if row.get("country_iso3") != manifest.get("country_iso3"):
                issues.append(_issue("BLOCK", "evidence_country_mismatch", "Evidence country_iso3 differs from manifest.", identifier, path))
            if row.get("country_confidence") not in {"High", "Medium"}:
                issues.append(_issue(
                    "BLOCK", "evidence_country_confidence_too_low",
                    "Included evidence country_confidence must be High or Medium.", identifier, path,
                ))
            if row.get("country_assignment_status") not in {"exact_country", "multi_country"}:
                issues.append(_issue(
                    "BLOCK", "evidence_country_assignment_unresolved",
                    "Included evidence must have exact_country or multi_country assignment.", identifier, path,
                ))
            if row.get("content_language") not in {"", "zh", "zh-CN", "zh-Hans"} and not row.get("original_text_translation_cn"):
                issues.append(_issue("WARN", "translation_missing", "Non-Chinese evidence lacks Chinese translation.", identifier, path))
            if not str(row.get("published_at", "")).strip() or row.get("date_confidence") in {
                "", "Month", "Relative-normalized", "Approximate", "Unknown",
            }:
                issues.append(_issue("WARN", "date_precision_low", "Evidence date is not exact.", identifier, path))

    for stream in ("A", "B", "C"):
        if not any(row.get("evidence_stream") == stream for row in included):
            issues.append(_issue("WARN", "stream_has_no_included_evidence", f"Stream {stream} has no Included evidence."))
    if included and not any(str(row.get("admin1_name", "")).strip() for row in included):
        issues.append(_issue(
            "WARN", "subnational_coverage_missing",
            "No Included evidence has an admin1_name; disclose that subnational coverage is absent.",
        ))
    for row in included:
        if row.get("evidence_stream") == "C" and not any(
            str(row.get(field, "")).strip()
            for field in (
                "visible_metrics_raw", "views_visible", "likes_visible", "comments_visible",
                "shares_visible", "clicks_visible", "followers_visible",
            )
        ):
            issues.append(_issue(
                "WARN", "kol_metrics_missing",
                "KOL/KOC evidence has no visible interaction or audience metric.",
                row.get("evidence_id", ""), EVIDENCE_PATHS["C"],
            ))
    return issues, all_evidence, included


def _coverage_rows(included: List[dict], source_registry: List[dict]) -> List[dict]:
    family_by_source = {row.get("source_id", ""): row.get("source_family", "") for row in source_registry}
    rows: List[dict] = []

    def add(dimension: str, category: str, count: int, family_count: int = 0, status: str = "PASS", note: str = "") -> None:
        rows.append({
            "dimension": dimension, "category": category, "required": "No", "attempted": "Yes",
            "included_count": str(count), "source_family_count": str(family_count) if family_count else "",
            "status": status, "gap_note": note,
        })

    for stream in ("A", "B", "C"):
        selected = [row for row in included if row.get("evidence_stream") == stream]
        families = {family_by_source.get(row.get("source_id", ""), "") for row in selected} - {""}
        add("evidence_stream", stream, len(selected), len(families), "PASS" if selected else "WARN", "No Included evidence." if not selected else "")
    for field, dimension in (
        ("content_language", "content_language"),
        ("admin1_name", "subnational"),
        ("audience_role", "audience_role"),
        ("normalized_theme", "normalized_theme"),
    ):
        counts = Counter(row.get(field, "") or "Unknown" for row in included)
        for category, count in sorted(counts.items()):
            selected = [row for row in included if (row.get(field, "") or "Unknown") == category]
            families = {family_by_source.get(row.get("source_id", ""), "") for row in selected} - {""}
            add(dimension, category, count, len(families))
    return rows


def _completeness_labels(issues: List[dict], tables: Dict[str, List[dict]]) -> List[str]:
    labels = set()
    for path in QUERY_PATHS.values():
        for row in tables.get(path, []):
            status = str(row.get("status", "")).lower()
            for label in ("ranking_limited", "access_limited", "budget_limited"):
                if label in status.replace("-", "_") or label.replace("_", "-") in status:
                    labels.add(label)
            notes = str(row.get("notes", "")).lower()
            for label in ("ranking_limited", "access_limited", "budget_limited"):
                if label in notes.replace("-", "_"):
                    labels.add(label)
    if any(issue["code"] == "date_precision_low" for issue in issues):
        labels.add("date_precision_limited")
    return sorted(labels)


def _write_quality_outputs(
    run_dir: Path,
    result: dict,
    coverage_rows: List[dict],
    templates_root: Path,
) -> None:
    quality_dir = Path(run_dir) / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        quality_dir / "coverage-matrix.csv",
        _header(Path(templates_root) / "coverage-matrix.csv"),
        coverage_rows,
    )
    temporary = quality_dir / ".structural-validation.json.tmp"
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(quality_dir / "structural-validation.json")

    grouped = {"BLOCK": [], "WARN": [], "INFO": []}
    for issue in result["issues"]:
        grouped.setdefault(issue["severity"], []).append(issue)
    lines = ["# 数据缺口与偏差（内部探索版）", ""]
    for severity in ("BLOCK", "WARN", "INFO"):
        lines.extend([f"## {severity}", ""])
        if not grouped[severity]:
            lines.append("无。")
        for issue in grouped[severity]:
            suffix = f" (`{issue.get('record_id')}`)" if issue.get("record_id") else ""
            lines.append(f"- **{issue['code']}**{suffix}: {issue['message']}")
        lines.append("")
    lines.extend([
        "## 使用边界", "",
        "本包仅用于内部探索。WARN 不阻止打包；BLOCK 必须修复。对外引用、正式传播或高风险市场决策前需另行完成人工证据复核。", "",
    ])
    (quality_dir / "gaps-and-biases.md").write_text("\n".join(lines), encoding="utf-8")


def _write_funnel(run_dir: Path, tables: Dict[str, List[dict]], included: List[dict], labels: List[str]) -> None:
    query_rows = [row for path in QUERY_PATHS.values() for row in tables.get(path, [])]
    raw_rows = tables.get("evidence/raw-discovery-log.csv", [])
    evidence_rows = [row for path in EVIDENCE_PATHS.values() for row in tables.get(path, [])]
    inspected = sum(_integer(row.get("results_inspected")) for row in query_rows)
    valid = sum(_integer(row.get("valid_results")) for row in query_rows)
    inclusion = Counter(row.get("inclusion_status", "") or "Unknown" for row in raw_rows)
    by_stream = Counter(row.get("evidence_stream", "") for row in included)
    lines = [
        "# 公开需求信号采集漏斗（内部探索版）", "",
        "本文件描述公开检索框的执行结果，不代表统计抽样或总体人口比例。", "",
        "| 层级 | 数量 |", "|---|---:|",
        f"| 查询记录 | {len(query_rows)} |",
        f"| 结果检查次数 | {inspected} |",
        f"| 查询级有效命中 | {valid} |",
        f"| 原始唯一内容 | {len(raw_rows)} |",
        f"| 正式纳入原始内容 | {inclusion.get('Included', 0)} |",
        f"| Candidate | {inclusion.get('Candidate', 0)} |",
        f"| Excluded | {inclusion.get('Excluded', 0)} |",
        f"| 编码证据记录 | {len(evidence_rows)} |",
        "",
        f"证据流：A {by_stream.get('A', 0)}、B {by_stream.get('B', 0)}、C {by_stream.get('C', 0)}。",
        "",
        "完整性标签：" + ("、".join(f"`{label}`" for label in labels) if labels else "无显式限制标签。"),
        "",
        "查询矩阵内所有符合规则且去重后的唯一命中应全部纳入；平台动态排序、登录限制和查询预算必须单独披露。", "",
    ]
    (Path(run_dir) / "05-collection-funnel.md").write_text("\n".join(lines), encoding="utf-8")


def validate_internal_run(run_dir: Path, config_root: Path, templates_root: Path) -> dict:
    run_dir = Path(run_dir)
    for relative in REQUIRED_NON_CSV:
        if not (run_dir / relative).exists():
            raise ManifestError(f"required run file not found: {run_dir / relative}")
    manifest = load_manifest(run_dir)
    config = load_country_config(Path(config_root), manifest["country_iso2"])
    plan = _load_plan(run_dir)

    issues, tables = _schema_issues(run_dir, Path(templates_root))
    query_issues, query_ids = _query_issues(config, tables)
    plan_issues, source_ids, source_roles = _source_and_plan_issues(plan, tables)
    evidence_issues, all_evidence, included = _evidence_issues(
        manifest, tables, source_ids, source_roles, query_ids
    )
    issues = _dedupe_issues(issues + query_issues + plan_issues + evidence_issues)

    family_by_source = {
        row.get("source_id", ""): row.get("source_family", "")
        for row in tables.get("02-source-discovery.csv", [])
    }
    themes = {
        row.get("normalized_theme", "")
        for row in included if str(row.get("normalized_theme", "")).strip()
    }
    for theme in sorted(themes):
        families = {
            family_by_source.get(row.get("source_id", ""), "")
            for row in included if row.get("normalized_theme") == theme
        } - {""}
        if len(families) < 2:
            issues.append(_issue(
                "WARN", "single_source_family_theme",
                f"Theme {theme} is supported by fewer than two source families.",
            ))

    iso2 = manifest.get("country_iso2", "")
    iso3 = manifest.get("country_iso3", "")
    if plan.get("country_iso2") and plan.get("country_iso2") != iso2:
        issues.append(_issue("BLOCK", "source_plan_country_mismatch", "Source plan country differs from manifest."))
    if plan.get("run_id") and plan.get("run_id") != manifest.get("run_id"):
        issues.append(_issue("BLOCK", "source_plan_run_mismatch", "Source plan run_id differs from manifest."))

    for relative, (_, id_field) in CSV_TABLES.items():
        for row in tables.get(relative, []):
            identifier = row.get(id_field, "")
            if id_field == "query_id":
                stream = row.get("evidence_stream", "")
                accepted = (f"Q-{stream}-{iso2}-", f"Q-{stream}-{iso3}-")
            else:
                stem = {"source_id": "SRC", "content_id": "CNT", "evidence_id": "EVD"}[id_field]
                accepted = (f"{stem}-{iso2}-", f"{stem}-{iso3}-")
            if identifier and not identifier.startswith(accepted):
                issues.append(_issue(
                    "BLOCK", "country_code_missing_from_id",
                    f"{id_field} must include ISO2 or ISO3 country code.", identifier, relative,
                ))

    issues = _dedupe_issues(issues)
    labels = _completeness_labels(issues, tables)
    coverage = _coverage_rows(included, tables.get("02-source-discovery.csv", []))
    counts = {
        "sources": len(tables.get("02-source-discovery.csv", [])),
        "queries": sum(len(tables.get(path, [])) for path in QUERY_PATHS.values()),
        "raw": len(tables.get("evidence/raw-discovery-log.csv", [])),
        "evidence": len(all_evidence),
        "included_evidence": len(included),
        "A": sum(row.get("evidence_stream") == "A" for row in included),
        "B": sum(row.get("evidence_stream") == "B" for row in included),
        "C": sum(row.get("evidence_stream") == "C" for row in included),
    }
    severity_counts = Counter(issue["severity"] for issue in issues)
    result = {
        "status": "internal_validation_block" if severity_counts.get("BLOCK") else (
            "internal_validation_warn" if severity_counts.get("WARN") else "internal_validation_pass"
        ),
        "internal_use_only": True,
        "run_id": manifest.get("run_id"),
        "country_iso2": iso2,
        "country_iso3": iso3,
        "validated_at": utc_now(),
        "counts": counts,
        "completeness_labels": labels,
        "severity_counts": dict(severity_counts),
        "issues": issues,
    }
    _write_quality_outputs(run_dir, result, coverage, Path(templates_root))
    _write_funnel(run_dir, tables, included, labels)
    return result
