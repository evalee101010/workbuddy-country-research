import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import yaml

from .manifest import (
    ManifestError,
    load_manifest,
    save_manifest,
    transition_state,
    utc_now,
)


QUERY_FILES = (
    "A-competitor-queries.csv",
    "B-local-needs-queries.csv",
    "C-kol-koc-queries.csv",
)
STREAMS = ("A", "B", "C")
CHANNEL_ROLES = {
    "Core",
    "Supplement",
    "Discovery-only",
    "Auth-optional",
    "Consent-required",
    "Reject",
}


def _read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_header(path: Path) -> List[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def _atomic_write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _atomic_write_yaml(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    temporary.replace(path)


def _integer(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def _yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1", "available"}


def _split_streams(value: object) -> List[str]:
    normalized = str(value or "").replace(",", "|")
    return [stream.strip() for stream in normalized.split("|") if stream.strip() in STREAMS]


def _access_role(source: dict) -> Optional[str]:
    access_text = " ".join(
        str(source.get(field, ""))
        for field in ("access_status", "public_access", "auth_or_rights")
    ).lower()
    if "consent-required" in access_text or "consent required" in access_text:
        return "Consent-required"
    if "private group" in access_text or "closed group" in access_text:
        return "Consent-required"
    if "auth-optional" in access_text or "login only" in access_text or "auth only" in access_text:
        return "Auth-optional"
    if str(source.get("access_status", "")).strip().lower() == "reject":
        return "Reject"
    return None


def _query_summary(run_dir: Path, name_to_id: Dict[str, str]) -> Dict[str, dict]:
    summaries: Dict[str, dict] = {}
    for filename in QUERY_FILES:
        for row in _read_csv(run_dir / "queries" / filename):
            source_identifier = name_to_id.get(row.get("source_name", ""))
            if not source_identifier:
                continue
            summary = summaries.setdefault(
                source_identifier,
                {"inspected": 0, "valid": 0, "valid_groups": set()},
            )
            inspected = _integer(row.get("results_inspected"))
            valid = _integer(row.get("valid_results"))
            summary["inspected"] += inspected
            summary["valid"] += valid
            if valid > 0:
                summary["valid_groups"].add(row.get("query_group", ""))
    return summaries


def _recommend(source: dict, pilot: dict, query: dict) -> tuple:
    access_role = _access_role(source)
    if access_role:
        return access_role, f"Access boundary requires {access_role}; it cannot be a Core public source."
    if source.get("local_role") == "recruitment_only":
        return "Discovery-only", "Ecosystem/directory source is suitable for finding actors, not direct demand claims."

    valid_groups = len(query.get("valid_groups", set()))
    valid_results = query.get("valid", 0)
    geo_count = _integer(pilot.get("high_geo_count")) + _integer(pilot.get("medium_geo_count"))
    provenance_ready = _yes(pilot.get("original_text_available")) and _yes(pilot.get("date_available"))
    repeatable = _yes(pilot.get("repeatable_discovery"))
    mainstream = _integer(pilot.get("mainstream_task_count")) > 0
    technical = (
        source.get("local_role") == "global_technical"
        or str(source.get("main_bias", "")).strip().lower() == "developer"
        or str(source.get("audience_profile", "")).strip().lower() == "developer"
    )
    migration_only = source.get("local_role") in {"migration_corridor", "diaspora"}

    core_ready = (
        valid_groups >= 2
        and valid_results > 0
        and geo_count > 0
        and provenance_ready
        and repeatable
        and mainstream
    )
    if core_ready and technical:
        return "Supplement", "Global technical/Developer source is capped at technical supplement."
    if core_ready and migration_only:
        return "Supplement", "Migration-corridor evidence cannot alone represent the country mainstream."
    if core_ready:
        return "Core", "Two or more valid query groups plus geo, provenance, date and repeatability checks passed."
    if valid_results > 0 and geo_count > 0 and provenance_ready:
        return "Supplement", "Valid country evidence exists, but one or more Core repeatability/coverage checks remain unmet."
    if valid_results > 0:
        return "Discovery-only", "Queries found material, but provenance or country attribution is not ready for direct coding."
    return "Reject", "No valid pilot result was recorded; keep out of formal collection until re-piloted."


def _seed_pilot_rows(run_dir: Path, registry: List[dict]) -> List[dict]:
    pilot_path = run_dir / "03-channel-fit-pilot.csv"
    fieldnames = _csv_header(pilot_path)
    existing = {row.get("source_id"): row for row in _read_csv(pilot_path) if row.get("source_id")}
    name_to_id = {row.get("source_name", ""): row["source_id"] for row in registry}
    summaries = _query_summary(run_dir, name_to_id)
    output = []
    for source in registry:
        identifier = source["source_id"]
        row = {field: "" for field in fieldnames}
        row.update(existing.get(identifier, {}))
        query = summaries.get(identifier, {"inspected": 0, "valid": 0, "valid_groups": set()})
        row.update({
            "source_id": identifier,
            "channel": source.get("source_name", ""),
            "source_family": source.get("source_family", ""),
            "evidence_streams": source.get("candidate_evidence_streams", ""),
            "access_status": source.get("access_status", ""),
            "query_groups_tested": str(len(query["valid_groups"])),
            "inspected_count": str(query["inspected"]),
            "raw_found_count": str(query["valid"]),
            "main_bias": row.get("main_bias") or source.get("main_bias", ""),
        })
        recommendation, automatic_reason = _recommend(source, row, query)
        row["pilot_recommendation"] = recommendation
        if not row.get("decision_reason"):
            row["decision_reason"] = automatic_reason
        if not row.get("captured_at") and query["inspected"]:
            row["captured_at"] = utc_now()
        output.append(row)
    _atomic_write_csv(pilot_path, fieldnames, output)
    return output


def _effective_role(source: dict, pilot: dict) -> str:
    proposed = str(pilot.get("final_role") or pilot.get("pilot_recommendation") or "Reject")
    if proposed not in CHANNEL_ROLES:
        raise ManifestError(f"invalid final_role for {source['source_id']}: {proposed}")
    boundary = _access_role(source)
    if boundary and proposed not in {boundary, "Reject"}:
        raise ManifestError(
            f"access boundary violation for {source['source_id']}: {boundary} cannot become {proposed}"
        )
    if source.get("local_role") == "global_technical" and proposed == "Core":
        raise ManifestError(f"global technical source cannot become country Core: {source['source_id']}")
    return proposed


def _build_plan(run_dir: Path, registry: List[dict], pilot_rows: List[dict]) -> dict:
    plan_path = run_dir / "04-approved-source-plan.yml"
    existing = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    by_source = {row["source_id"]: row for row in registry}
    streams = {}
    recommendations = []
    anonymous_sources: Set[str] = set()
    rejected = []

    for stream in STREAMS:
        previous = (existing.get("streams") or {}).get(stream, {})
        streams[stream] = {
            "core": [],
            "supplement": [],
            "discovery_only": [],
            "auth_optional": [],
            "consent_required": [],
            "documented_gap": previous.get("documented_gap", ""),
        }

    for pilot in pilot_rows:
        source = by_source[pilot["source_id"]]
        role = _effective_role(source, pilot)
        source_streams = _split_streams(pilot.get("evidence_streams"))
        recommendations.append({
            "source_id": pilot["source_id"],
            "source_name": pilot.get("channel", ""),
            "role": role,
            "streams": source_streams,
            "access_status": pilot.get("access_status", ""),
            "main_bias": pilot.get("main_bias", ""),
            "decision_reason": pilot.get("decision_reason", ""),
        })
        if role == "Reject":
            rejected.append(pilot["source_id"])
            continue
        role_key = {
            "Core": "core",
            "Supplement": "supplement",
            "Discovery-only": "discovery_only",
            "Auth-optional": "auth_optional",
            "Consent-required": "consent_required",
        }[role]
        for stream in source_streams:
            streams[stream][role_key].append(pilot["source_id"])
        if role in {"Core", "Supplement"} and _access_role(source) is None:
            anonymous_sources.add(pilot["source_id"])

    return {
        "version": existing.get("version", 1),
        "run_id": existing.get("run_id", load_manifest(run_dir)["run_id"]),
        "country_iso2": existing.get("country_iso2", load_manifest(run_dir)["country_iso2"]),
        "generated_at": utc_now(),
        "anonymous_path_status": "ready" if anonymous_sources else "gap",
        "anonymous_sources": sorted(anonymous_sources),
        "streams": streams,
        "source_decisions": recommendations,
        "rejected_sources": sorted(rejected),
        "approval_status": existing.get("approval_status", "pending"),
        "approved_by": existing.get("approved_by", ""),
        "approved_at": existing.get("approved_at", ""),
        "approval_note": existing.get("approval_note", ""),
    }


def _approve_if_ready(run_dir: Path, plan: dict) -> bool:
    status = str(plan.get("approval_status", "pending")).strip().lower()
    if status != "approved":
        return False
    if not plan.get("approved_by") or not plan.get("approved_at"):
        raise ManifestError("Gate A approval requires approved_by and approved_at")
    if plan.get("anonymous_path_status") != "ready":
        raise ManifestError("Gate A approval requires at least one executable anonymous public source")
    for stream in STREAMS:
        stream_plan = plan["streams"][stream]
        if not stream_plan.get("core") and not str(stream_plan.get("documented_gap", "")).strip():
            raise ManifestError(f"Gate A requires a Core source or documented_gap for stream {stream}")
    return True


def pilot_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    if manifest["state"] not in {"discovery_ready", "source_plan_pending", "source_plan_approved"}:
        raise ManifestError(f"pilot is not allowed from state {manifest['state']}")

    registry = _read_csv(run_dir / "02-source-discovery.csv")
    pilot_rows = _seed_pilot_rows(run_dir, registry)
    plan = _build_plan(run_dir, registry, pilot_rows)
    _atomic_write_yaml(run_dir / "04-approved-source-plan.yml", plan)

    if manifest["state"] == "discovery_ready":
        transition_state(
            run_dir,
            "source_plan_pending",
            "Channel-fit pilot summarized; executor source decisions pending",
        )

    if _approve_if_ready(run_dir, plan):
        current = load_manifest(run_dir)
        if current["state"] == "source_plan_pending":
            transition_state(run_dir, "source_plan_approved", "Gate A source plan approved")
        current = load_manifest(run_dir)
        current["approvals"]["source_plan"] = {
            "status": "approved",
            "by": plan["approved_by"],
            "at": plan["approved_at"],
        }
        current["updated_at"] = utc_now()
        save_manifest(run_dir, current)
        return {"status": "source_plan_approved", "sources": len(pilot_rows)}

    return {"status": "source_plan_pending", "sources": len(pilot_rows)}
