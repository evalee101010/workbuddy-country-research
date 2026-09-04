import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set
from urllib.parse import urlsplit

from .csvio import read_csv, read_header, write_csv
from .discovery import source_id
from .ids import canonicalize_url, content_id, duplicate_hints, evidence_id
from .manifest import ManifestError, assert_run_writable, load_manifest, utc_now


SOURCE_FILES = {
    "raw_feedback": "04-raw-feedback.csv",
    "coded_feedback": "05-coded-feedback.csv",
    "kol_koc": "16-kol-uae-multichannel-samples.csv",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _empty_row(template_path: Path) -> dict:
    return {field: "" for field in read_header(template_path)}


def _json_source(row: dict) -> str:
    return json.dumps({"legacy_source_row": row}, ensure_ascii=False, sort_keys=True)


def _country_assignment(country_iso3: str, confidence: str) -> str:
    if country_iso3 == "ARE" and confidence in {"High", "Medium"}:
        return "exact_country"
    return "unresolved"


def _inclusion(value: str) -> str:
    lowered = str(value or "").lower()
    if lowered.startswith("included"):
        return "Included"
    if lowered.startswith("excluded"):
        return "Excluded"
    if "candidate" in lowered:
        return "Candidate"
    return "Needs-review"


def _kol_date_confidence(value: str) -> str:
    value = str(value or "")
    if len(value) == 10:
        return "Exact"
    if len(value) == 7:
        return "Month"
    return "Unknown"


def _source_identifier(name: str) -> str:
    return source_id("ARE", name or "Unknown legacy source")


def _legacy_content_identifier(source_name: str, legacy_id: str, url: str) -> str:
    # Several legacy review records point to a paginated listing rather than a
    # unique permalink. The legacy ID is therefore the safest immutable surrogate.
    return content_id(source_name, platform_content_id=f"legacy:{legacy_id}", item_url=url)


def _cross_scope_id(url: str) -> str:
    canonical = canonicalize_url(url)
    if not canonical:
        return ""
    return content_id("canonical-url", item_url=canonical).replace("CNT-", "XSC-")


def _map_raw_feedback(row: dict, run_id: str, template: Path) -> dict:
    legacy_id = row.get("feedback_id", "")
    source_name = row.get("source_channel") or row.get("source_name") or "Legacy feedback"
    item_url = row.get("source_url", "")
    identifier = _legacy_content_identifier(source_name, legacy_id, item_url)
    output = _empty_row(template)
    output.update({
        "content_id": identifier,
        "legacy_record_id": legacy_id,
        "run_id": run_id,
        "source_id": _source_identifier(source_name),
        "source_type": source_name,
        "source_name": source_name,
        "source_url": item_url,
        "item_url": item_url,
        "canonical_url": canonicalize_url(item_url),
        "author_alias": row.get("author_alias", ""),
        "published_at": row.get("published_at", ""),
        "published_at_raw": row.get("published_at_raw", ""),
        "date_confidence": row.get("date_confidence", ""),
        "captured_at": row.get("captured_at", ""),
        "query_language": row.get("query_language", ""),
        "content_language": row.get("content_language", ""),
        "original_text": row.get("original_text", ""),
        "original_text_translation_cn": row.get("original_text_translation_cn", ""),
        "context_note": row.get("evidence_excerpt", ""),
        "country_iso3": row.get("country_iso3_candidate", ""),
        "country_or_region": row.get("geo_claim", ""),
        "geo_evidence": row.get("geo_evidence", ""),
        "country_confidence": row.get("country_confidence", ""),
        "scope_level": "country" if row.get("country_iso3_candidate") == "ARE" else "global_unknown",
        "scope_name": row.get("country_iso3_candidate") or row.get("geo_claim", ""),
        "discovery_round": "legacy-uae-pilot",
        "country_assignment_status": _country_assignment(
            row.get("country_iso3_candidate", ""), row.get("country_confidence", "")
        ),
        "duplicate_group": row.get("duplicate_group", ""),
        "inclusion_status": _inclusion(row.get("inclusion_status", "")),
        "review_status": "Pending",
        "capture_mode": row.get("capture_mode", ""),
        "raw_fields_json": _json_source(row),
        "researcher_note": row.get("researcher_note", ""),
    })
    return output


def _map_coded_feedback(row: dict, raw_by_legacy: Dict[str, dict], run_id: str, template: Path) -> dict:
    legacy_id = row.get("feedback_id", "")
    raw = raw_by_legacy.get(legacy_id, {})
    source_name = raw.get("source_name") or row.get("source_name") or "Legacy feedback"
    item_url = raw.get("item_url") or row.get("source_url", "")
    content_identifier = raw.get("content_id") or _legacy_content_identifier(source_name, legacy_id, item_url)
    output = _empty_row(template)
    shared = {
        "evidence_id": evidence_id(content_identifier, f"legacy feedback {legacy_id}"),
        "content_id": content_identifier,
        "legacy_record_id": legacy_id,
        "run_id": run_id,
        "evidence_stream": "A",
        "source_id": raw.get("source_id") or _source_identifier(source_name),
        "source_type": row.get("source_type", ""),
        "source_name": source_name,
        "source_url": row.get("source_url", ""),
        "item_url": item_url,
        "author_alias": raw.get("author_alias", ""),
        "published_at": row.get("published_at", ""),
        "published_at_raw": raw.get("published_at_raw", ""),
        "date_confidence": row.get("date_confidence", ""),
        "captured_at": row.get("captured_at", ""),
        "query_language": row.get("query_language", ""),
        "content_language": row.get("content_language", ""),
        "original_text": raw.get("original_text", ""),
        "original_text_translation_cn": raw.get("original_text_translation_cn", ""),
        "context_note": raw.get("context_note", ""),
        "country_iso3": row.get("country_iso3", ""),
        "country_or_region": row.get("country_or_region", ""),
        "geo_evidence": row.get("geo_evidence", ""),
        "country_confidence": row.get("country_confidence", ""),
        "scope_level": "country" if row.get("country_iso3") == "ARE" else "global_unknown",
        "scope_name": row.get("country_iso3") or row.get("country_or_region", ""),
        "discovery_round": "legacy-uae-pilot",
        "country_assignment_status": _country_assignment(
            row.get("country_iso3", ""), row.get("country_confidence", "")
        ),
        "audience_role": row.get("user_role", ""),
        "technical_level": "Unknown",
        "source_audience_bias": row.get("source_bias_note", ""),
        "duplicate_group": raw.get("duplicate_group", ""),
        "inclusion_status": _inclusion(row.get("inclusion_status", "")),
        "review_status": "Pending",
        "researcher_note": row.get("researcher_note", ""),
    }
    output.update(shared)
    for target, source in {
        "product": "product",
        "product_tier": "product_tier",
        "company_size": "company_size",
        "job_to_be_done": "job_to_be_done",
        "trigger": "trigger",
        "input_or_connected_tools": "input_or_connected_tools",
        "expected_output": "expected_output",
        "actual_result": "actual_result",
        "success_status": "success_status",
        "failure_stage": "failure_stage",
        "manual_interventions": "manual_interventions",
        "time_or_latency": "time_or_latency",
        "setup_difficulty": "setup_difficulty",
        "reliability": "reliability",
        "control_and_approval": "control_and_approval",
        "privacy_and_trust": "privacy_and_trust",
        "pricing_or_usage_limit": "pricing_or_usage_limit",
        "current_alternative": "current_alternative",
        "retention_churn_or_switching_signal": "retention_churn_or_switching_signal",
        "sentiment": "sentiment",
    }.items():
        output[target] = row.get(source, "")
    output["headline_evidence"] = "No"
    output["normalized_theme"] = row.get("evidence_excerpt", "")
    return output


def _map_kol_raw(row: dict, run_id: str, template: Path) -> dict:
    legacy_id = row.get("sample_id", "")
    source_name = row.get("platform", "") or "Legacy KOL/KOC"
    item_url = row.get("url", "")
    identifier = _legacy_content_identifier(source_name, legacy_id, item_url)
    confidence = row.get("audience_geo_confidence", "")
    output = _empty_row(template)
    output.update({
        "content_id": identifier,
        "legacy_record_id": legacy_id,
        "run_id": run_id,
        "source_id": _source_identifier(source_name),
        "source_type": row.get("content_type", ""),
        "source_name": source_name,
        "source_url": item_url,
        "item_url": item_url,
        "canonical_url": canonicalize_url(item_url),
        "author_alias": row.get("owner_name", ""),
        "published_at": row.get("published_at", ""),
        "published_at_raw": row.get("published_at", ""),
        "date_confidence": _kol_date_confidence(row.get("published_at", "")),
        "captured_at": row.get("captured_at", ""),
        "content_language": "",
        "original_text": row.get("original_text_excerpt", ""),
        "original_text_translation_cn": row.get("original_text_translation_cn", ""),
        "context_note": row.get("caveat", ""),
        "country_iso3": "ARE",
        "country_or_region": "United Arab Emirates",
        "admin1_name": row.get("emirate_name", ""),
        "admin1_confidence": confidence,
        "geo_evidence": row.get("geography_evidence", ""),
        "country_confidence": confidence,
        "scope_level": row.get("scope_level", ""),
        "scope_name": row.get("scope_id", ""),
        "discovery_round": "legacy-uae-kol-pilot",
        "source_native_geo_granularity": row.get("scope_level", ""),
        "country_assignment_status": _country_assignment("ARE", confidence),
        "cross_scope_duplicate_id": _cross_scope_id(item_url),
        "source_audience_bias": "",
        "inclusion_status": _inclusion(row.get("inclusion_status", "")),
        "review_status": "Pending",
        "capture_mode": "Legacy public-page review",
        "raw_fields_json": _json_source(row),
        "researcher_note": row.get("caveat", ""),
    })
    return output


def _map_kol_evidence(row: dict, raw: dict, run_id: str, template: Path) -> dict:
    legacy_id = row.get("sample_id", "")
    output = _empty_row(template)
    for field in (
        "content_id", "legacy_record_id", "run_id", "source_id", "source_type", "source_name",
        "source_url", "item_url", "author_alias", "published_at", "published_at_raw",
        "date_confidence", "captured_at", "query_language", "content_language", "original_text",
        "original_text_translation_cn", "context_note", "country_iso3", "country_or_region",
        "admin1_name", "admin1_confidence", "city_name", "geo_evidence", "country_confidence",
        "scope_level", "scope_name", "discovery_round", "source_native_geo_granularity",
        "country_assignment_status", "origin_market", "destination_market", "cross_scope_duplicate_id",
        "audience_role", "technical_level", "source_audience_bias", "duplicate_group",
        "inclusion_status", "review_status", "researcher_note",
    ):
        output[field] = raw.get(field, "")
    output.update({
        "evidence_id": evidence_id(raw["content_id"], f"legacy KOL/KOC {legacy_id}"),
        "evidence_stream": "C",
        "creator_name": row.get("owner_name", ""),
        "creator_type": row.get("owner_type", ""),
        "content_format": row.get("content_type", ""),
        "work_scene": row.get("scene_labels", ""),
        "visible_metrics_raw": " ".join(
            part for part in (row.get("visible_metric_label", ""), row.get("visible_metric_value", "")) if part
        ),
        "metric_captured_at": row.get("captured_at", ""),
        "commercial_interest": row.get("commercial_interest", ""),
        "commercial_bias": row.get("caveat", ""),
        "headline_evidence": "No",
    })
    metric_label = str(row.get("visible_metric_label", "")).lower()
    metric_value = row.get("visible_metric_value", "")
    metric_fields = {
        "view": "views_visible",
        "like": "likes_visible",
        "comment": "comments_visible",
        "share": "shares_visible",
        "click": "clicks_visible",
        "follower": "followers_visible",
    }
    for marker, field in metric_fields.items():
        if marker in metric_label:
            output[field] = metric_value
            break
    return output


def _upsert(path: Path, new_rows: Iterable[dict]) -> None:
    existing = read_csv(path)
    by_legacy = {row.get("legacy_record_id"): row for row in existing if row.get("legacy_record_id")}
    unkeyed = [row for row in existing if not row.get("legacy_record_id")]
    for row in new_rows:
        by_legacy.setdefault(row.get("legacy_record_id"), row)
    write_csv(path, read_header(path), unkeyed + [by_legacy[key] for key in sorted(by_legacy)])


def _platform_family(name: str) -> str:
    lowered = name.lower()
    if "trustpilot" in lowered or "app store" in lowered or "google play" in lowered:
        return "review_platform"
    if name in {"LinkedIn"}:
        return "professional_social"
    if name in {"Instagram", "YouTube", "Spotify"}:
        return "creator_social"
    if name in {"Reddit", "UAE local Reddit", "Telegram"}:
        return "forum_social"
    if name == "Topmate":
        return "creator_commerce"
    return "public_web"


def _upsert_legacy_sources(run_dir: Path, raw_feedback: List[dict], kol_rows: List[dict]) -> None:
    path = run_dir / "02-source-discovery.csv"
    existing = read_csv(path)
    by_id = {row["source_id"]: row for row in existing if row.get("source_id")}
    platforms: Dict[str, dict] = {}
    for row in raw_feedback:
        name = row.get("source_channel") or row.get("source_name") or "Legacy feedback"
        platforms.setdefault(name, {"url": row.get("source_url", ""), "streams": {"A"}})
    for row in kol_rows:
        name = row.get("platform") or "Legacy KOL/KOC"
        platforms.setdefault(name, {"url": row.get("url", ""), "streams": set()})
        platforms[name]["streams"].add("C")
    header = read_header(path)
    for name, details in platforms.items():
        identifier = _source_identifier(name)
        if identifier in by_id:
            continue
        blank = {field: "" for field in header}
        blank.update({
            "source_id": identifier,
            "country_iso3": "ARE",
            "source_name": name,
            "source_url": details["url"],
            "source_family": _platform_family(name),
            "local_role": "legacy_country_pilot",
            "local_activity_evidence": "Captured in the 2026 UAE legacy pilot; current activity must be revalidated.",
            "audience_profile": "Unknown; preserve source-specific bias.",
            "candidate_evidence_streams": "|".join(sorted(details["streams"])),
            "access_status": "Reference-Only",
            "public_access": "Legacy public-page capture",
            "machine_access": "Not assumed",
            "auth_or_rights": "Revalidate before new collection",
            "extractable_fields": "Only fields present in legacy capture",
            "main_bias": "Legacy pilot selection",
            "pilot_status": "Legacy-imported",
            "researcher_note": "Migration does not preapprove this source for a new country run.",
        })
        by_id[identifier] = blank
    write_csv(path, header, [by_id[key] for key in sorted(by_id)])


def _unmapped_fields(rows: List[dict], consumed: Set[str]) -> List[str]:
    if not rows:
        return []
    fields = set().union(*(row.keys() for row in rows))
    return sorted(field for field in fields if field not in consumed)


def _write_log(
    run_dir: Path,
    before_hashes: dict,
    after_hashes: dict,
    counts: dict,
    hints: List[dict],
    raw_rows: List[dict],
    unmapped: dict,
) -> None:
    legacy_by_content = {row["content_id"]: row["legacy_record_id"] for row in raw_rows}
    lines = [
        "# Legacy UAE Migration Log",
        "",
        f"Generated at: {utc_now()}",
        "",
        "## Source integrity",
        "",
    ]
    for name in SOURCE_FILES.values():
        status = "unchanged" if before_hashes[name] == after_hashes[name] else "CHANGED"
        lines.append(f"- `{name}`: `{before_hashes[name]}` → `{after_hashes[name]}` ({status})")
    lines.extend(["", "## Row reconciliation", ""])
    lines.append(
        f"- Source rows: raw feedback {counts['source']['raw_feedback']}; coded feedback {counts['source']['coded_feedback']}; KOL/KOC {counts['source']['kol_koc']}."
    )
    lines.append(
        f"- Migrated rows: raw {counts['output']['raw']}; A {counts['output']['A']}; C {counts['output']['C']}."
    )
    lines.extend(["", "## Duplicate hints (no rows deleted)", ""])
    if hints:
        for hint in hints:
            ids = [legacy_by_content.get(identifier, identifier) for identifier in hint["content_ids"]]
            lines.append(f"- {hint['reason']}: {', '.join(ids)}")
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Unmapped legacy fields", ""])
    for source, fields in unmapped.items():
        lines.append(f"- {source}: {', '.join(fields) if fields else 'None'}")
    lines.extend([
        "",
        "All legacy rows are also preserved in `raw_fields_json`; an unmapped field is not discarded.",
        "",
    ])
    (run_dir / "review" / "legacy-uae-migration.md").write_text("\n".join(lines), encoding="utf-8")


def migrate_uae(source_root: Path, run_dir: Path) -> dict:
    source_root = Path(source_root)
    run_dir = Path(run_dir)
    assert_run_writable(run_dir)
    manifest = load_manifest(run_dir)
    if manifest.get("country_iso2") != "AE":
        raise ManifestError("migrate-uae can only target an AE run")

    paths = {key: source_root / filename for key, filename in SOURCE_FILES.items()}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise ManifestError(f"legacy UAE source file missing: {', '.join(missing)}")
    before_hashes = {path.name: _sha256(path) for path in paths.values()}
    raw_feedback = read_csv(paths["raw_feedback"])
    coded_feedback = read_csv(paths["coded_feedback"])
    kol_rows = read_csv(paths["kol_koc"])
    run_id = manifest["run_id"]

    raw_template = run_dir / "evidence" / "raw-discovery-log.csv"
    a_template = run_dir / "evidence" / "A-competitor-feedback.csv"
    c_template = run_dir / "evidence" / "C-kol-koc-content.csv"
    migrated_raw_feedback = [_map_raw_feedback(row, run_id, raw_template) for row in raw_feedback]
    raw_by_legacy = {row["legacy_record_id"]: row for row in migrated_raw_feedback}
    migrated_a = [
        _map_coded_feedback(row, raw_by_legacy, run_id, a_template) for row in coded_feedback
    ]
    migrated_kol_raw = [_map_kol_raw(row, run_id, raw_template) for row in kol_rows]
    migrated_c = [
        _map_kol_evidence(source, raw, run_id, c_template)
        for source, raw in zip(kol_rows, migrated_kol_raw)
    ]
    migrated_raw = migrated_raw_feedback + migrated_kol_raw

    _upsert(raw_template, migrated_raw)
    _upsert(a_template, migrated_a)
    _upsert(c_template, migrated_c)
    _upsert_legacy_sources(run_dir, raw_feedback, kol_rows)

    hints = duplicate_hints(migrated_raw)
    after_hashes = {path.name: _sha256(path) for path in paths.values()}
    if before_hashes != after_hashes:
        raise ManifestError("legacy source files changed during migration")

    consumed = {
        "raw_feedback": {
            "feedback_id", "source_channel", "source_name", "source_url", "author_alias",
            "published_at", "published_at_raw", "date_confidence", "captured_at", "query_language",
            "content_language", "original_text", "original_text_translation_cn", "evidence_excerpt",
            "country_iso3_candidate", "geo_claim", "geo_evidence", "country_confidence",
            "duplicate_group", "inclusion_status", "capture_mode", "researcher_note",
        },
        "coded_feedback": set(coded_feedback[0].keys()) if coded_feedback else set(),
        "kol_koc": {
            "sample_id", "platform", "scope_id", "scope_level", "emirate_name", "content_type",
            "owner_name", "owner_type", "url", "published_at", "visible_metric_label",
            "visible_metric_value", "scene_labels", "geography_evidence", "audience_geo_confidence",
            "commercial_interest", "original_text_excerpt", "original_text_translation_cn",
            "inclusion_status", "caveat", "captured_at",
        },
    }
    unmapped = {
        "04-raw-feedback.csv": _unmapped_fields(raw_feedback, consumed["raw_feedback"]),
        "05-coded-feedback.csv": _unmapped_fields(coded_feedback, consumed["coded_feedback"]),
        "16-kol-uae-multichannel-samples.csv": _unmapped_fields(kol_rows, consumed["kol_koc"]),
    }
    counts = {
        "source": {
            "raw_feedback": len(raw_feedback),
            "coded_feedback": len(coded_feedback),
            "kol_koc": len(kol_rows),
        },
        "output": {"raw": len(migrated_raw), "A": len(migrated_a), "C": len(migrated_c)},
    }
    _write_log(run_dir, before_hashes, after_hashes, counts, hints, migrated_raw, unmapped)
    return {
        "status": "migrated",
        "source_rows": counts["source"],
        "output_rows": counts["output"],
        "duplicate_hint_count": len(hints),
        "log": str(run_dir / "review" / "legacy-uae-migration.md"),
    }
