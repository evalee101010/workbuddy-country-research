import hashlib
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import yaml

from .config import load_country_config


class ManifestError(RuntimeError):
    """Raised for unsafe run selection or invalid state transitions."""


ALLOWED_TRANSITIONS = {
    "initialized": {"discovery_ready"},
    "discovery_ready": {"source_plan_pending"},
    "source_plan_pending": {"source_plan_approved"},
    "source_plan_approved": {"collection_in_progress"},
    "collection_in_progress": {"validation_pass", "validation_warn", "validation_block"},
    "validation_block": {"collection_in_progress", "validation_pass", "validation_warn"},
    "validation_pass": {"frozen"},
    "validation_warn": {"frozen"},
    "frozen": set(),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_yaml(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def load_manifest(run_dir: Path) -> dict:
    path = Path(run_dir) / "00-run-manifest.yml"
    if not path.exists():
        raise ManifestError(f"manifest not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "state" not in payload:
        raise ManifestError(f"invalid manifest: {path}")
    return payload


def save_manifest(run_dir: Path, manifest: dict) -> None:
    assert_run_writable(run_dir, allow_frozen_write=False)
    _atomic_write_yaml(Path(run_dir) / "00-run-manifest.yml", manifest)


def assert_run_writable(run_dir: Path, allow_frozen_write: bool = False) -> None:
    manifest = load_manifest(run_dir)
    if manifest.get("state") == "frozen" and not allow_frozen_write:
        raise ManifestError(f"run is frozen and immutable: {run_dir}")


def transition_state(run_dir: Path, new_state: str, note: str = "") -> dict:
    manifest = load_manifest(run_dir)
    current = manifest["state"]
    if new_state not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ManifestError(f"invalid state transition: {current} -> {new_state}")
    manifest["state"] = new_state
    manifest["updated_at"] = utc_now()
    manifest.setdefault("state_history", []).append(
        {"from": current, "to": new_state, "at": manifest["updated_at"], "note": note}
    )
    _atomic_write_yaml(Path(run_dir) / "00-run-manifest.yml", manifest)
    return manifest


def resolve_run_dir(runs_root: Path, country_code: str, run_id: Optional[str] = None) -> Path:
    country = country_code.upper()
    country_root = Path(runs_root) / country
    if run_id:
        run_dir = country_root / run_id
        if not run_dir.exists():
            raise ManifestError(f"run not found: {country}/{run_id}")
        return run_dir
    active = []
    if country_root.exists():
        for candidate in sorted(path for path in country_root.iterdir() if path.is_dir()):
            try:
                if load_manifest(candidate).get("state") != "frozen":
                    active.append(candidate)
            except ManifestError:
                continue
    if not active:
        raise ManifestError(f"no active run for {country}; pass --run-id or run init")
    if len(active) > 1:
        ids = ", ".join(path.name for path in active)
        raise ManifestError(f"multiple active runs for {country}: {ids}; pass --run-id")
    return active[0]


def _copy_template(templates_root: Path, source_name: str, destination: Path) -> None:
    source = Path(templates_root) / source_name
    if not source.exists():
        raise ManifestError(f"required template not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _render_context(template: str, config: dict, run_id: str, research_window: dict) -> str:
    identity = config["identity"]
    replacements = {
        "{{country_name_cn}}": identity["name_cn"],
        "{{country_name_en}}": identity["name_en"],
        "{{country_iso3}}": identity["iso3"],
        "{{run_id}}": run_id,
        "{{window_start}}": str(research_window["start"]),
        "{{window_end}}": str(research_window["end"]),
        "{{core_languages}}": ", ".join(config["languages"]["core"]),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def initialize_run(
    country_code: str,
    run_id: str,
    runs_root: Path,
    config_root: Path,
    templates_root: Path,
    researcher: str = "Unknown",
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
) -> Path:
    country = country_code.upper()
    config = load_country_config(Path(config_root), country)
    research_window = {
        "start": str(window_start or config["research"]["window_start"]),
        "end": str(window_end or config["research"]["window_end"]),
    }
    try:
        parsed_start = date.fromisoformat(research_window["start"])
        parsed_end = date.fromisoformat(research_window["end"])
    except ValueError as error:
        raise ManifestError("research window dates must use YYYY-MM-DD") from error
    if parsed_start > parsed_end:
        raise ManifestError("research window start must be on or before end")
    country_root = Path(runs_root) / country
    run_dir = country_root / run_id
    if run_dir.exists():
        raise ManifestError(f"refusing to overwrite existing run: {run_dir}")
    country_root.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()

    for directory in ("queries", "evidence", "review", "output"):
        (run_dir / directory).mkdir()

    copies = {
        "02-source-discovery.csv": "source-discovery.csv",
        "03-channel-fit-pilot.csv": "channel-fit-pilot.csv",
        "evidence/raw-discovery-log.csv": "raw-discovery-log.csv",
        "evidence/A-competitor-feedback.csv": "A-competitor-feedback.csv",
        "evidence/B-local-work-needs.csv": "B-local-work-needs.csv",
        "evidence/C-kol-koc-content.csv": "C-kol-koc-content.csv",
        "review/evidence-audit.csv": "evidence-audit.csv",
        "review/coverage-matrix.csv": "coverage-matrix.csv",
        "review/gaps-and-biases.md": "gaps-and-biases.md",
        "queries/A-competitor-queries.csv": "A-competitor-queries.csv",
        "queries/B-local-needs-queries.csv": "B-local-needs-queries.csv",
        "queries/C-kol-koc-queries.csv": "C-kol-koc-queries.csv",
    }
    for destination, source in copies.items():
        _copy_template(templates_root, source, run_dir / destination)

    context_template = (Path(templates_root) / "country-context.md").read_text(encoding="utf-8")
    (run_dir / "01-country-context.md").write_text(
        _render_context(context_template, config, run_id, research_window), encoding="utf-8"
    )

    source_plan = yaml.safe_load(
        (Path(templates_root) / "source-plan.yml").read_text(encoding="utf-8")
    )
    source_plan["run_id"] = run_id
    source_plan["country_iso2"] = country
    _atomic_write_yaml(run_dir / "04-approved-source-plan.yml", source_plan)

    created_at = utc_now()
    config_path = Path(config_root) / "countries" / f"{country}.yml"
    codebook_path = Path(config_root) / "global" / "codebook.yml"
    quality_path = Path(config_root) / "global" / "quality-rules.yml"
    manifest = {
        "version": 1,
        "run_id": run_id,
        "country_iso2": country,
        "country_iso3": config["identity"]["iso3"],
        "created_at": created_at,
        "updated_at": created_at,
        "state": "initialized",
        "config_version": config.get("version", 1),
        "codebook_version": 1,
        "researcher": researcher or "Unknown",
        "reviewer": "",
        "research_window": research_window,
        "anonymous_path_status": "ready",
        "auth_optional_status": "not_required",
        "input_hashes": {
            "country_config": sha256_file(config_path),
            "codebook": sha256_file(codebook_path),
            "quality_rules": sha256_file(quality_path),
        },
        "approvals": {
            "source_plan": {"status": "pending", "by": "", "at": ""},
            "evidence_audit": {"status": "pending", "by": "", "at": ""},
        },
        "warnings": [],
        "state_history": [],
        "frozen_at": "",
    }
    _atomic_write_yaml(run_dir / "00-run-manifest.yml", manifest)
    (run_dir / "99-change-and-freeze-log.md").write_text(
        f"# Change and Freeze Log\n\n- {created_at}: run initialized by {researcher or 'Unknown'}.\n",
        encoding="utf-8",
    )
    return run_dir
