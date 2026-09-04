from collections import Counter
from pathlib import Path
from typing import Iterable, List

import yaml

from .config import load_country_config
from .csvio import read_csv
from .manifest import load_manifest


EVIDENCE_FILES = {
    "A": "A-competitor-feedback.csv",
    "B": "B-local-work-needs.csv",
    "C": "C-kol-koc-content.csv",
}
QUERY_FILES = {
    "A": "A-competitor-queries.csv",
    "B": "B-local-needs-queries.csv",
    "C": "C-kol-koc-queries.csv",
}


def _yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1"}


def _included(run_dir: Path) -> List[dict]:
    rows = []
    for stream, filename in EVIDENCE_FILES.items():
        for row in read_csv(run_dir / "evidence" / filename):
            if row.get("inclusion_status") == "Included":
                row = dict(row)
                row["evidence_stream"] = row.get("evidence_stream") or stream
                rows.append(row)
    return rows


def _is_technical(row: dict) -> bool:
    return (
        row.get("technical_level") in {"Technical", "Developer"}
        or row.get("audience_role") == "developers"
        or str(row.get("source_audience_bias", "")).strip().lower() == "developer"
    )


def _is_advanced(row: dict) -> bool:
    return row.get("technical_level") == "No-code-capable" or row.get("mainstream_fit") == "Advanced-workflow"


def _query_status(run_dir: Path, stream: str) -> str:
    rows = read_csv(run_dir / "queries" / QUERY_FILES[stream])
    executed = [
        row for row in rows
        if str(row.get("status", "")).lower() not in {"", "planned", "not-run", "not run"}
        or str(row.get("results_inspected", "")).strip() not in {"", "0"}
    ]
    inspected = sum(int(row.get("results_inspected") or 0) for row in executed)
    valid = sum(int(row.get("valid_results") or 0) for row in executed)
    return f"已执行查询 {len(executed)}/{len(rows)}；查看结果 {inspected}；记录有效发现 {valid}。"


def _metrics(row: dict) -> str:
    labels = (
        ("views", "views_visible"),
        ("likes", "likes_visible"),
        ("comments", "comments_visible"),
        ("shares", "shares_visible"),
        ("clicks", "clicks_visible"),
        ("followers", "followers_visible"),
    )
    return ", ".join(f"{label}={row.get(field) or 'Unknown'}" for label, field in labels)


def _evidence_cards(rows: Iterable[dict], include_metrics: bool = False) -> List[str]:
    output = []
    for row in rows:
        headline = "标题证据" if _yes(row.get("headline_evidence")) else "补充证据"
        output.append(
            f"- **{row.get('evidence_id') or 'Missing evidence_id'}**（{headline}；{row.get('source_name') or 'Unknown source'}；地域置信度 {row.get('country_confidence') or 'Unknown'}）"
        )
        output.append(f"  - 任务/主题：{row.get('normalized_theme') or row.get('job_to_be_done') or row.get('work_scene') or '未编码'}")
        if include_metrics:
            output.append(f"  - 平台内可见指标（逐条，不跨平台汇总）：{_metrics(row)}")
            output.append(
                f"  - CTA/承接：{row.get('cta_type') or 'Unknown'} / {row.get('offer_name') or row.get('offer_type') or 'Unknown'}"
            )
        output.append(f"  - 原话：{row.get('original_text') or '[缺失]'}")
        output.append(f"  - 中文：{row.get('original_text_translation_cn') or '[未提供]'}")
        output.append(f"  - 回源：[{row.get('content_id') or 'Missing content_id'}]({row.get('item_url') or row.get('source_url') or ''})")
    return output


def _stream_section(run_dir: Path, plan: dict, stream: str, rows: List[dict]) -> List[str]:
    output = [_query_status(run_dir, stream), ""]
    mainstream = [row for row in rows if row.get("evidence_stream") == stream and not _is_technical(row)]
    if not mainstream:
        gap = str((plan.get("streams") or {}).get(stream, {}).get("documented_gap", "")).strip()
        output.append("本证据线暂无合格 Included 记录。")
        output.append(f"Gate A 缺口：{gap or '尚未填写；在正式交付前必须说明。'}")
        return output
    output.extend(_evidence_cards(mainstream, include_metrics=stream == "C"))
    return output


def _demote_headings(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            lines.append("#### " + line[3:])
        elif line.startswith("# "):
            lines.append("### " + line[2:])
        else:
            lines.append(line)
    return "\n".join(lines)


def render_markdown(run_dir: Path, config_root: Path) -> str:
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    config = load_country_config(Path(config_root), manifest["country_iso2"])
    plan = yaml.safe_load(
        (run_dir / "04-approved-source-plan.yml").read_text(encoding="utf-8")
    ) or {}
    evidence = _included(run_dir)
    mainstream = [row for row in evidence if not _is_technical(row) and not _is_advanced(row)]
    advanced = [row for row in evidence if _is_advanced(row) and not _is_technical(row)]
    technical = [row for row in evidence if _is_technical(row)]
    source_rows = read_csv(run_dir / "02-source-discovery.csv")
    pilot_rows = read_csv(run_dir / "03-channel-fit-pilot.csv")
    role_counts = Counter(row.get("audience_role") or "Unknown" for row in mainstream)

    lines = [
        f"# {config['identity']['name_cn']} Cowork 公开需求信号国家反馈包",
        "",
        f"> Run `{manifest['run_id']}` · 状态 `{manifest['state']}` · 研究窗口 {manifest['research_window']['start']} 至 {manifest['research_window']['end']}",
        "",
        "## 1. 研究摘要",
        "",
        f"本包纳入 {len(evidence)} 条证据单元，其中主流非开发者 {len(mainstream)} 条、进阶工作流 {len(advanced)} 条、技术补充 {len(technical)} 条。它描述公开可见信号及其边界，不估计市场份额或总体需求规模。",
        "",
        "## 2. 研究范围与方法",
        "",
        "按国家颗粒度先完成当地渠道发现、Channel Fit Pilot 与 Gate A，再分别采集 A 竞品实际使用反馈、B 当地工作需求、C KOL/KOC 内容及商业承接。国家证据与地区/语区/迁移走廊信号分层保存。",
        "",
        f"核心查询语言：{', '.join(config['languages']['core'])}；探索语言：{', '.join(config['languages'].get('exploratory', [])) or '无'}；迁移走廊语言：{', '.join(config['languages'].get('migration_corridor', [])) or '无'}。",
        "",
        "## 3. 当地渠道与 Gate A",
        "",
        f"发现注册来源 {len(source_rows)} 个；完成渠道角色记录 {len(pilot_rows)} 个；匿名路径状态：`{plan.get('anonymous_path_status', 'Unknown')}`。",
        "",
    ]
    for stream in ("A", "B", "C"):
        stream_plan = (plan.get("streams") or {}).get(stream, {})
        lines.append(
            f"- {stream}：Core {', '.join(stream_plan.get('core') or []) or '无'}；Supplement {', '.join(stream_plan.get('supplement') or []) or '无'}。"
        )
    lines.extend(["", "## 4. A：竞品实际使用反馈", ""])
    lines.extend(_stream_section(run_dir, plan, "A", evidence))
    lines.extend(["", "## 5. B：当地工作需求", ""])
    lines.extend(_stream_section(run_dir, plan, "B", evidence))
    lines.extend(["", "## 6. C：KOL/KOC 内容与商业承接", ""])
    lines.extend(_stream_section(run_dir, plan, "C", evidence))
    lines.extend(["", "## 7. 主流非开发者人群", ""])
    if role_counts:
        lines.extend(f"- {role}: {count} 条合格证据。" for role, count in sorted(role_counts.items()))
        lines.extend(_evidence_cards(mainstream))
    else:
        lines.append("暂无可归入主流非开发者人群的合格证据；不得用开发者来源补齐。")
    lines.extend(["", "## 8. 进阶工作流", ""])
    if advanced:
        lines.extend(_evidence_cards(advanced))
    else:
        lines.append("暂无单独编码的 No-code/业务 AI 进阶工作流证据。")
    lines.extend(["", "## 9. 技术补充", ""])
    if technical:
        lines.append("以下信号只进入技术附录，不单独支撑大众市场结论。")
        lines.extend(_evidence_cards(technical))
    else:
        lines.append("本轮未纳入开发者或技术社区证据。")
    lines.extend(["", "## 10. 覆盖、缺口与偏差", ""])
    gaps_path = run_dir / "review" / "gaps-and-biases.md"
    lines.append(_demote_headings(gaps_path.read_text(encoding="utf-8")) if gaps_path.exists() else "尚未运行 Gate B；覆盖状态待生成。")
    lines.extend(["", "## 11. 引用索引", ""])
    if evidence:
        lines.append("| Evidence ID | Content ID | 证据线 | 原话（最短必要片段） | URL |")
        lines.append("|---|---|---|---|---|")
        for row in evidence:
            original = str(row.get("original_text") or "").replace("|", "\\|").replace("\n", " ")
            url = row.get("item_url") or row.get("source_url") or ""
            lines.append(
                f"| {row.get('evidence_id')} | {row.get('content_id')} | {row.get('evidence_stream')} | {original} | [回源]({url}) |"
            )
    else:
        lines.append("暂无 Included 证据，引用索引保持为空。")
    lines.append("")
    return "\n".join(lines)


def write_markdown(run_dir: Path, config_root: Path, output_path: Path) -> None:
    Path(output_path).write_text(render_markdown(run_dir, config_root), encoding="utf-8")
