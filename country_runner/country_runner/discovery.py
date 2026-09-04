import csv
import hashlib
import re
from pathlib import Path
from typing import Dict, Iterable, List

from .config import load_country_config
from .manifest import ManifestError, load_manifest, transition_state, utc_now


QUERY_FILENAMES = {
    "A": "A-competitor-queries.csv",
    "B": "B-local-needs-queries.csv",
    "C": "C-kol-koc-queries.csv",
}


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if normalized:
        return normalized[:40]
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def source_id(iso3: str, name: str) -> str:
    return f"SRC-{iso3}-{_slug(name)}"


def _read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _atomic_write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _language_items(config: dict) -> List[dict]:
    items = []
    for role in ("core", "exploratory", "migration_corridor"):
        for code in config["languages"].get(role, []):
            items.append({"code": code, "role": role})
    return items


def _term_for_language(task: dict, language: str) -> str:
    terms = task.get("terms", {})
    candidates = terms.get(language) or terms.get(language.split("-")[0]) or terms.get("en")
    if candidates:
        return candidates[0]
    for values in terms.values():
        if values:
            return values[0]
    return task["id"].replace("_", " ")


def _anchor_for_language(config: dict, language: str) -> str:
    if language == "en":
        return config["identity"]["name_en"]
    non_ascii = [
        anchor for anchor in config["geography"]["country_anchors"]
        if any(ord(character) > 127 for character in str(anchor))
    ]
    return str(non_ascii[0] if non_ascii else config["geography"]["country_anchors"][0])


def _query_text(
    stream: str,
    channel: dict,
    task_term: str,
    scope_anchor: str,
    product: str,
) -> str:
    platform = channel["name"]
    if stream == "A":
        return f'"{product}" {task_term} {scope_anchor} review experience problem {platform}'
    if stream == "B":
        return f'{task_term} {scope_anchor} work problem workflow AI {platform}'
    return f'{task_term} {scope_anchor} AI tutorial template course mentor {platform}'


def _make_query_row(
    config: dict,
    channel: dict,
    stream: str,
    task: dict,
    language: dict,
    query_group: str,
    scope_level: str,
    scope_name: str,
    scope_anchor: str,
    admin1_name: str = "",
    product: str = "",
) -> dict:
    task_term = _term_for_language(task, language["code"])
    stable_key = "|".join([
        config["identity"]["iso3"], channel["name"], stream, query_group,
        language["code"], scope_name, task["id"], product,
    ])
    query_id = f"Q-{stream}-{hashlib.sha1(stable_key.encode('utf-8')).hexdigest()[:12]}"
    return {
        "query_id": query_id,
        "query_group": query_group,
        "evidence_stream": stream,
        "source_name": channel["name"],
        "source_family": channel["family"],
        "source_scope_default": channel["scope_default"],
        "scope_level": scope_level,
        "scope_name": scope_name,
        "admin1_name": admin1_name,
        "query_language": language["code"],
        "language_role": language["role"],
        "task_family": task["id"],
        "product": product,
        "query": _query_text(stream, channel, task_term, scope_anchor, product),
        "access_mode": channel["access_mode"],
        "status": "Planned",
        "results_inspected": "",
        "valid_results": "",
        "notes": "Country/source terms are discovery context; item-level geo evidence is still required.",
    }


def generate_queries(config: dict) -> Dict[str, List[dict]]:
    output = {"A": [], "B": [], "C": []}
    tasks = config["task_families"]
    languages = _language_items(config)
    core_languages = [item for item in languages if item["role"] == "core"]
    primary_language = core_languages[0]
    identity = config["identity"]
    direct_products = config["products"]["direct"]

    for channel_index, channel in enumerate(config["channels"]):
        for stream in channel["candidate_streams"]:
            for language_index, language in enumerate(languages):
                repetitions = 2 if language["role"] == "core" else 1
                for repetition in range(repetitions):
                    task = tasks[(channel_index + language_index + repetition) % len(tasks)]
                    product = ""
                    if stream == "A":
                        product = direct_products[(channel_index + language_index + repetition) % len(direct_products)]
                    output[stream].append(_make_query_row(
                        config=config,
                        channel=channel,
                        stream=stream,
                        task=task,
                        language=language,
                        query_group=f"country-{language['role']}-{repetition + 1}",
                        scope_level="country",
                        scope_name=identity["iso3"],
                        scope_anchor=_anchor_for_language(config, language["code"]),
                        product=product,
                    ))

            for admin_index, admin1 in enumerate(config["geography"].get("admin1", [])):
                task = tasks[(channel_index + admin_index) % len(tasks)]
                product = direct_products[(channel_index + admin_index) % len(direct_products)] if stream == "A" else ""
                output[stream].append(_make_query_row(
                    config=config,
                    channel=channel,
                    stream=stream,
                    task=task,
                    language=primary_language,
                    query_group="subnational-probe",
                    scope_level="subnational",
                    scope_name=admin1["name_en"],
                    scope_anchor=str(admin1["anchors"][0]),
                    admin1_name=admin1["name_en"],
                    product=product,
                ))
    return output


def _seed_registry(run_dir: Path, config: dict) -> int:
    path = run_dir / "02-source-discovery.csv"
    existing = _read_csv(path)
    fieldnames = list(existing[0]) if existing else []
    if not fieldnames:
        with path.open(encoding="utf-8", newline="") as handle:
            fieldnames = next(csv.reader(handle))
    by_id = {row["source_id"]: row for row in existing if row.get("source_id")}
    for channel in config["channels"]:
        identifier = source_id(config["identity"]["iso3"], channel["name"])
        if identifier in by_id:
            continue
        by_id[identifier] = {
            "source_id": identifier,
            "country_iso3": config["identity"]["iso3"],
            "source_name": channel["name"],
            "source_url": channel["url"],
            "source_family": channel["family"],
            "local_role": channel["scope_default"],
            "local_activity_evidence": "To be verified in country pilot",
            "audience_profile": channel["audience_bias"],
            "query_languages": "|".join(item["code"] for item in _language_items(config)),
            "source_native_geo_granularity": "unknown",
            "candidate_evidence_streams": "|".join(channel["candidate_streams"]),
            "access_status": "Candidate-Validate",
            "public_access": channel["access_mode"],
            "machine_access": "Not assumed",
            "auth_or_rights": "Review before scale",
            "extractable_fields": "To be tested",
            "freshness_window": str(config["research"]["window_start"]),
            "main_bias": channel["audience_bias"],
            "pilot_status": "Not-run",
            "researcher_note": channel["seed_reason"],
        }
    rows = [by_id[key] for key in sorted(by_id)]
    _atomic_write_csv(path, fieldnames, rows)
    return len(rows)


def discover_run(run_dir: Path, config_root: Path) -> dict:
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    if manifest["state"] not in {"initialized", "discovery_ready"}:
        raise ManifestError(f"discover is not allowed from state {manifest['state']}")
    config = load_country_config(Path(config_root), manifest["country_iso2"])
    source_count = _seed_registry(run_dir, config)
    query_sets = generate_queries(config)
    for stream, rows in query_sets.items():
        path = run_dir / "queries" / QUERY_FILENAMES[stream]
        with path.open(encoding="utf-8", newline="") as handle:
            fieldnames = next(csv.reader(handle))
        _atomic_write_csv(path, fieldnames, rows)
    if manifest["state"] == "initialized":
        transition_state(run_dir, "discovery_ready", "Local source registry and query packs generated")
    return {
        "status": "discovery_ready",
        "sources": source_count,
        "queries": {stream: len(rows) for stream, rows in query_sets.items()},
        "generated_at": utc_now(),
    }
