from pathlib import Path
from typing import Callable, Optional

from .manifest import ManifestError, load_manifest, save_manifest, sha256_file, transition_state, utc_now
from .report_md import write_markdown
from .report_xlsx import build_xlsx


def build_run(
    run_dir: Path,
    config_root: Path,
    xlsx_builder: Optional[Callable[[Path, Path], None]] = None,
) -> dict:
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    if manifest["state"] not in {"validation_pass", "validation_warn"}:
        raise ManifestError(f"build requires validation_pass or validation_warn; current state is {manifest['state']}")
    if manifest.get("approvals", {}).get("source_plan", {}).get("status") != "approved":
        raise ManifestError("build requires signed Gate A source-plan approval")
    if manifest.get("approvals", {}).get("evidence_audit", {}).get("status") != "approved":
        raise ManifestError("build requires signed Gate B evidence-audit approval")
    if not manifest.get("reviewer"):
        raise ManifestError("build requires a named Gate B reviewer")

    output_dir = run_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    final_md = output_dir / "country-feedback-pack.md"
    final_xlsx = output_dir / "country-feedback-pack.xlsx"
    temporary_md = output_dir / ".country-feedback-pack.md.tmp"
    temporary_xlsx = output_dir / ".country-feedback-pack.tmp.xlsx"
    write_markdown(run_dir, Path(config_root), temporary_md)
    builder = xlsx_builder or build_xlsx
    try:
        builder(run_dir, temporary_xlsx)
        if not temporary_xlsx.exists():
            raise ManifestError("XLSX builder did not create its requested output")
        temporary_md.replace(final_md)
        temporary_xlsx.replace(final_xlsx)
        temporary_inspection = output_dir / ".country-feedback-pack.tmp-inspection.json"
        temporary_previews = output_dir / ".country-feedback-pack.tmp-previews"
        if temporary_inspection.exists():
            temporary_inspection.replace(output_dir / "country-feedback-pack-inspection.json")
        if temporary_previews.exists():
            temporary_previews.rename(output_dir / "country-feedback-pack-previews")
        temporary_artifact_inspection = Path(str(temporary_xlsx) + ".inspect.ndjson")
        if temporary_artifact_inspection.exists():
            temporary_artifact_inspection.replace(Path(str(final_xlsx) + ".inspect.ndjson"))
    except Exception:
        temporary_md.unlink(missing_ok=True)
        temporary_xlsx.unlink(missing_ok=True)
        raise

    frozen_at = utc_now()
    manifest = load_manifest(run_dir)
    manifest["frozen_at"] = frozen_at
    manifest["output_hashes"] = {
        "markdown": sha256_file(final_md),
        "xlsx": sha256_file(final_xlsx),
    }
    manifest["updated_at"] = frozen_at
    save_manifest(run_dir, manifest)
    log_path = run_dir / "99-change-and-freeze-log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"- {frozen_at}: country pack built and frozen after {manifest['state']} by {manifest['reviewer']}.\n"
        )
    transition_state(run_dir, "frozen", "Country feedback pack built and frozen")
    return {
        "status": "frozen",
        "markdown": str(final_md),
        "xlsx": str(final_xlsx),
    }
