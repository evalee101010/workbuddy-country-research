import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlsplit

import yaml

from .config import load_country_config
from .coverage import build_coverage, write_coverage
from .csvio import read_csv, read_header, write_csv
from .manifest import (
    ManifestError,
    load_manifest,
    save_manifest,
    transition_state,
    utc_now,
)


EVIDENCE_FILES = {
    "A": "A-competitor-feedback.csv",
    "B": "B-local-work-needs.csv",
    "C": "C-kol-koc-content.csv",
}
AUDIT_CHECKS = ("provenance_ok", "translation_ok", "geo_ok", "audience_ok", "dedup_ok")


def _issue(severity: str, code: str, message: str, evidence_id: str = "") -> dict:
    issue = {"severity": severity, "code": code, "message": message}
    if evidence_id:
        issue["evidence_id"] = evidence_id
    return issue


def _yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1", "pass"}


def _valid_url(value: str) -> bool:
    try:
        parts = urlsplit(str(value or "").strip())
        return parts.scheme in {"http", "https"} and bool(parts.netloc)
    except ValueError:
        return False


def _load_evidence(run_dir: Path) -> List[dict]:
    rows = []
    for stream, filename in EVIDENCE_FILES.items():
        for row in read_csv(run_dir / "evidence" / filename):
            row = dict(row)
            row["evidence_stream"] = row.get("evidence_stream") or stream
            rows.append(row)
    return rows


def _stable_sample(rows: List[dict], count: int) -> set:
    ranked = sorted(
        rows,
        key=lambda row: hashlib.sha256(row.get("evidence_id", "").encode("utf-8")).hexdigest(),
    )
    return {row.get("evidence_id", "") for row in ranked[:count]}


def _seed_audit(run_dir: Path, evidence: List[dict]) -> List[dict]:
    path = run_dir / "review" / "evidence-audit.csv"
    existing = {row.get("evidence_id"): row for row in read_csv(path) if row.get("evidence_id")}
    included = [row for row in evidence if row.get("inclusion_status") == "Included"]
    headlines = {row.get("evidence_id") for row in included if _yes(row.get("headline_evidence"))}
    nonheadline = [row for row in included if row.get("evidence_id") not in headlines]
    sample_count = math.ceil(len(nonheadline) * 0.10) if nonheadline else 0
    sampled = _stable_sample(nonheadline, sample_count)
    fieldnames = read_header(path)
    output = []
    for evidence_row in included:
        identifier = evidence_row.get("evidence_id", "")
        row = {field: "" for field in fieldnames}
        row.update(existing.get(identifier, {}))
        row.update({
            "evidence_id": identifier,
            "content_id": evidence_row.get("content_id", ""),
            "evidence_stream": evidence_row.get("evidence_stream", ""),
            "headline_evidence": "Yes" if identifier in headlines else "No",
        })
        if not row.get("direct_quote"):
            row["direct_quote"] = "No"
        required = identifier in headlines or identifier in sampled or _yes(row.get("direct_quote"))
        row["required_review"] = "Yes" if required else "No"
        if not row.get("review_status"):
            row["review_status"] = "Pending"
        output.append(row)
    write_csv(path, fieldnames, output)
    return output


def _audit_issues(audit_rows: List[dict]) -> tuple:
    issues = []
    required = [row for row in audit_rows if _yes(row.get("required_review"))]
    signed = True
    reviewers = set()
    reviewed_times = []
    if not required:
        signed = False
    for row in required:
        status = row.get("review_status", "")
        identifier = row.get("evidence_id", "")
        if status not in {"Reviewed-pass", "Reviewed-warn"}:
            signed = False
            if status == "Reviewed-block" or str(row.get("issue_level", "")).upper() == "BLOCK":
                issues.append(_issue("BLOCK", "audit_row_blocked", "Reviewer marked evidence as blocked.", identifier))
            continue
        if not row.get("reviewer") or not row.get("reviewed_at"):
            signed = False
            continue
        if not all(_yes(row.get(field)) for field in AUDIT_CHECKS):
            signed = False
            issues.append(_issue(
                "BLOCK", "audit_check_failed",
                "Required provenance/translation/geo/audience/dedup review checks were not all passed.",
                identifier,
            ))
            continue
        reviewers.add(row["reviewer"])
        reviewed_times.append(row["reviewed_at"])
        if status == "Reviewed-warn" or str(row.get("issue_level", "")).upper() == "WARN":
            issues.append(_issue("WARN", "audit_row_warning", row.get("notes") or "Reviewer approved with warning.", identifier))
    if not signed:
        issues.append(_issue(
            "BLOCK", "reviewer_signature_missing",
            "All headline/direct-quote evidence and the deterministic sample require signed human review.",
        ))
    signature = {
        "approved": signed,
        "reviewer": ", ".join(sorted(reviewers)),
        "reviewed_at": max(reviewed_times) if reviewed_times else "",
    }
    return issues, signature


def _weak_geo_basis(text: str) -> bool:
    value = str(text or "").lower()
    weak = ("language", "domain", "storefront", "regioncode", "region code", "locale")
    strong = ("profile", "lives in", "based in", "client in", "works in", "author states", "post says")
    return any(marker in value for marker in weak) and not any(marker in value for marker in strong)


def _evidence_issues(run_dir: Path, config: dict, evidence: List[dict]) -> List[dict]:
    issues: List[dict] = []
    included = [row for row in evidence if row.get("inclusion_status") == "Included"]
    raw_rows = read_csv(run_dir / "evidence" / "raw-discovery-log.csv")
    raw_counts = Counter(row.get("content_id", "") for row in raw_rows if row.get("content_id"))
    raw_ids = set(raw_counts)
    for identifier, count in raw_counts.items():
        if count > 1:
            issues.append(_issue("BLOCK", "duplicate_content_id", f"Raw content_id appears {count} times: {identifier}"))
    evidence_counts = Counter(row.get("evidence_id", "") for row in evidence if row.get("evidence_id"))
    for identifier, count in evidence_counts.items():
        if count > 1:
            issues.append(_issue("BLOCK", "duplicate_evidence_id", f"evidence_id appears {count} times: {identifier}", identifier))

    plan = yaml.safe_load(
        (run_dir / "04-approved-source-plan.yml").read_text(encoding="utf-8")
    ) or {}
    decisions = {
        row.get("source_id"): row.get("role")
        for row in plan.get("source_decisions", [])
        if row.get("source_id")
    }
    source_registry = {
        row.get("source_id"): row for row in read_csv(run_dir / "02-source-discovery.csv")
    }

    themes: Dict[str, set] = defaultdict(set)
    for row in included:
        identifier = row.get("evidence_id", "")
        headline = _yes(row.get("headline_evidence"))
        required = {
            "content_id": "missing_content_id",
            "original_text": "missing_original_text",
            "item_url": "missing_item_url",
            "published_at": "missing_published_at",
            "geo_evidence": "missing_geo_evidence",
        }
        for field, code in required.items():
            if not str(row.get(field, "")).strip():
                issues.append(_issue("BLOCK", code, f"Included evidence is missing {field}.", identifier))
        if row.get("content_id") and row["content_id"] not in raw_ids:
            issues.append(_issue(
                "BLOCK", "raw_provenance_missing",
                "Encoded evidence does not link to a raw-discovery record.", identifier,
            ))
        if row.get("item_url") and not _valid_url(row["item_url"]):
            issues.append(_issue("BLOCK", "invalid_item_url", "item_url is not a valid HTTP(S) URL.", identifier))
        if headline and not str(row.get("context_note", "")).strip():
            issues.append(_issue("BLOCK", "headline_context_missing", "Headline evidence lacks necessary context.", identifier))
        if headline and row.get("country_confidence") not in {"High", "Medium"}:
            issues.append(_issue(
                "BLOCK", "headline_low_geo_confidence",
                "Country headline evidence must have High or Medium geo confidence.", identifier,
            ))
        if row.get("scope_level") in {"country", "subnational"} and _weak_geo_basis(row.get("geo_evidence", "")):
            issues.append(_issue(
                "BLOCK", "weak_geo_basis",
                "Language, domain, storefront, locale or regionCode alone cannot establish country attribution.",
                identifier,
            ))
        if headline and (
            row.get("technical_level") == "Developer"
            or row.get("audience_role") == "developers"
            or str(row.get("source_audience_bias", "")).lower() == "developer"
            or source_registry.get(row.get("source_id"), {}).get("local_role") == "global_technical"
        ):
            issues.append(_issue(
                "BLOCK", "developer_only_mainstream_claim",
                "Developer-only evidence cannot independently support a mainstream country headline.", identifier,
            ))
        if row.get("content_language") not in {"", "zh", "zh-CN", "zh-Hans"} and not str(
            row.get("original_text_translation_cn", "")
        ).strip():
            severity = "BLOCK" if headline else "WARN"
            issues.append(_issue(
                severity, "translation_missing",
                "Non-Chinese evidence lacks a traceable Chinese translation.", identifier,
            ))
        if row.get("date_confidence") in {"Month", "Relative-normalized", "Approximate", "Unknown", ""}:
            issues.append(_issue(
                "WARN", "date_precision_low",
                "Evidence date is not exact; disclose temporal uncertainty.", identifier,
            ))
        role = decisions.get(row.get("source_id"))
        if role == "Consent-required":
            issues.append(_issue(
                "BLOCK", "access_boundary_violation",
                "Consent-required source cannot enter Included evidence without a documented consent workflow.", identifier,
            ))
        if role == "Auth-optional" and not str(row.get("capture_mode", "")).lower().startswith("authorized"):
            issues.append(_issue(
                "WARN", "optional_auth_source_used",
                "Auth-optional evidence lacks an explicit authorized capture note.", identifier,
            ))
        theme = str(row.get("normalized_theme", "")).strip()
        if headline and theme:
            family = source_registry.get(row.get("source_id"), {}).get("source_family", "")
            themes[theme].add(family or row.get("source_id", ""))

    for theme, families in themes.items():
        if len(families) < 2:
            issues.append(_issue(
                "WARN", "single_source_theme",
                f"Headline theme '{theme}' is supported by only one source family.",
            ))
    c_rows = [row for row in included if row.get("evidence_stream") == "C"]
    if c_rows and any(
        not any(str(row.get(field, "")).strip() for field in (
            "views_visible", "likes_visible", "comments_visible", "shares_visible", "clicks_visible"
        ))
        for row in c_rows
    ):
        issues.append(_issue(
            "INFO", "kol_optional_metrics_missing",
            "Some KOL/KOC rows have no public interaction metrics; this does not block the anonymous path.",
        ))
    return issues


def _write_gaps(run_dir: Path, issues: List[dict]) -> None:
    grouped = {"BLOCK": [], "WARN": [], "INFO": []}
    for issue in issues:
        grouped.setdefault(issue["severity"], []).append(issue)
    lines = ["# 数据缺口与偏差", ""]
    for severity in ("BLOCK", "WARN", "INFO"):
        lines.extend([f"## {severity}", ""])
        if grouped[severity]:
            for issue in grouped[severity]:
                suffix = f" (`{issue['evidence_id']}`)" if issue.get("evidence_id") else ""
                lines.append(f"- **{issue['code']}**{suffix}: {issue['message']}")
        else:
            lines.append("无。")
        lines.append("")
    lines.extend([
        "## 授权增强缺口",
        "",
        "匿名公开路径不因可选 API、登录或付费数据缺失而中断。",
        "",
    ])
    (run_dir / "review" / "gaps-and-biases.md").write_text("\n".join(lines), encoding="utf-8")


def _dedupe_issues(issues: Iterable[dict]) -> List[dict]:
    output = []
    seen = set()
    for issue in issues:
        key = (issue.get("severity"), issue.get("code"), issue.get("message"), issue.get("evidence_id", ""))
        if key not in seen:
            seen.add(key)
            output.append(issue)
    return output


def validate_run(run_dir: Path, config_root: Path) -> dict:
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    if manifest["state"] not in {
        "source_plan_approved", "collection_in_progress", "validation_block",
        "validation_pass", "validation_warn",
    }:
        raise ManifestError(f"validate requires Gate A approval; current state is {manifest['state']}")
    if manifest["state"] in {"validation_pass", "validation_warn"}:
        raise ManifestError("validated run must be built/frozen or replaced by a new run")
    if manifest["state"] == "source_plan_approved":
        transition_state(run_dir, "collection_in_progress", "Evidence collection/import started")

    config = load_country_config(Path(config_root), manifest["country_iso2"])
    evidence = _load_evidence(run_dir)
    audit_rows = _seed_audit(run_dir, evidence)
    issues = _evidence_issues(run_dir, config, evidence)
    coverage_rows, coverage_issues = build_coverage(run_dir, config, evidence)
    write_coverage(run_dir, coverage_rows)
    audit_issues, signature = _audit_issues(audit_rows)
    issues = _dedupe_issues(issues + coverage_issues + audit_issues)
    _write_gaps(run_dir, issues)

    severities = {issue["severity"] for issue in issues}
    if "BLOCK" in severities:
        outcome = "validation_block"
    elif "WARN" in severities:
        outcome = "validation_warn"
    else:
        outcome = "validation_pass"

    validation_result = {
        "status": outcome,
        "evidence_count": len(evidence),
        "audit_count": len(audit_rows),
        "issues": issues,
        "severity_counts": dict(Counter(issue["severity"] for issue in issues)),
    }
    validation_path = run_dir / "review" / "validation-result.json"
    temporary_validation = validation_path.with_name(".validation-result.json.tmp")
    temporary_validation.write_text(
        json.dumps(validation_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_validation.replace(validation_path)

    current = load_manifest(run_dir)
    if current["state"] == "collection_in_progress":
        transition_state(run_dir, outcome, "Gate B validation completed")
    elif current["state"] == "validation_block" and outcome != "validation_block":
        transition_state(run_dir, outcome, "Gate B blockers resolved")
    current = load_manifest(run_dir)
    current["warnings"] = sorted({issue["code"] for issue in issues if issue["severity"] in {"WARN", "INFO"}})
    if signature["approved"]:
        current["reviewer"] = signature["reviewer"]
        current["approvals"]["evidence_audit"] = {
            "status": "approved",
            "by": signature["reviewer"],
            "at": signature["reviewed_at"],
        }
    current["updated_at"] = utc_now()
    save_manifest(run_dir, current)
    return validation_result
