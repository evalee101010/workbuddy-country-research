import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from typing import Dict, Iterable, List
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "dclid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "si",
    "feature",
    "ref",
    "ref_src",
    "source",
}
LANGUAGE_PATH_SEGMENTS = {
    "ar", "de", "en", "es", "fr", "hi", "id", "ja", "ml", "pt", "pt-br", "ur", "zh",
    "zh-cn", "zh-hans", "zh-hant",
}


def _digest(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _normalized_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    return re.sub(r"\s+", " ", normalized)


def canonicalize_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parts = urlsplit(raw)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host == "m.youtube.com":
        host = "youtube.com"
    port = parts.port
    netloc = host
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = f"{host}:{port}"

    path = re.sub(r"/{2,}", "/", parts.path or "/")
    path = quote(unquote(path), safe="/~:@!$&'()*+,;=-._")
    pairs = []
    for key, val in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_PARAMETERS:
            continue
        if lowered in {"lang", "locale", "hl"}:
            continue
        pairs.append((key, val))

    if host == "youtu.be":
        video_id = path.strip("/").split("/")[0]
        host = "youtube.com"
        netloc = host
        path = "/watch"
        pairs = [(key, val) for key, val in pairs if key != "v"] + [("v", video_id)]
    elif host == "youtube.com":
        match = re.match(r"/(?:shorts|embed)/([^/]+)", path)
        if match:
            path = "/watch"
            pairs = [(key, val) for key, val in pairs if key != "v"] + [("v", match.group(1))]

    query = urlencode(sorted(pairs))
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, query, ""))


def content_id(
    source_name: str,
    platform_content_id: str = "",
    item_url: str = "",
) -> str:
    source = _normalized_text(source_name)
    native = _normalized_text(platform_content_id)
    if native:
        identity = f"native|{source}|{native}"
    else:
        canonical = canonicalize_url(item_url)
        if not canonical:
            raise ValueError("content_id requires platform_content_id or item_url")
        identity = f"url|{canonical}"
    return f"CNT-{_digest(identity)}"


def evidence_id(content_identifier: str, coding_unit_key: str) -> str:
    content = str(content_identifier or "").strip()
    unit = _normalized_text(coding_unit_key)
    if not content or not unit:
        raise ValueError("evidence_id requires content_id and a non-empty coding unit key")
    return f"EVD-{_digest(f'{content}|{unit}') }"


def _query_ids(value: object) -> List[str]:
    return [item.strip() for item in str(value or "").replace(",", "|").split("|") if item.strip()]


def _record_conflict(record: dict, field: str, value: object) -> None:
    if value in (None, ""):
        return
    payload = {}
    if record.get("raw_fields_json"):
        try:
            loaded = json.loads(record["raw_fields_json"])
            if isinstance(loaded, dict):
                payload = loaded
        except (TypeError, ValueError):
            payload = {"legacy_raw_fields": record["raw_fields_json"]}
    conflicts = payload.setdefault("merge_conflicts", {})
    values = conflicts.setdefault(field, [])
    if value not in values:
        values.append(value)
    record["raw_fields_json"] = json.dumps(payload, ensure_ascii=False, sort_keys=True)


def merge_raw_records(rows: Iterable[dict]) -> List[dict]:
    merged: Dict[str, dict] = {}
    order: List[str] = []
    for source_row in rows:
        row = dict(source_row)
        identifier = row.get("content_id") or content_id(
            source_name=row.get("source_name", ""),
            platform_content_id=row.get("platform_content_id", ""),
            item_url=row.get("item_url") or row.get("canonical_url", ""),
        )
        row["content_id"] = identifier
        if row.get("item_url"):
            row["canonical_url"] = canonicalize_url(row["item_url"])
        if identifier not in merged:
            merged[identifier] = row
            order.append(identifier)
            continue

        target = merged[identifier]
        hit_ids = sorted(set(_query_ids(target.get("query_hit_ids"))) | set(_query_ids(row.get("query_hit_ids"))))
        target["query_hit_ids"] = "|".join(hit_ids)
        for field, value in row.items():
            if field in {"content_id", "query_hit_ids"} or value in (None, ""):
                continue
            if target.get(field) in (None, ""):
                target[field] = value
            elif target[field] != value:
                _record_conflict(target, field, value)
    return [merged[identifier] for identifier in order]


def _mirror_url_key(url: str) -> str:
    canonical = canonicalize_url(url)
    if not canonical:
        return ""
    parts = urlsplit(canonical)
    segments = [segment for segment in parts.path.split("/") if segment]
    if segments and segments[0].lower() in LANGUAGE_PATH_SEGMENTS:
        segments = segments[1:]
    return urlunsplit((parts.scheme, parts.netloc, "/" + "/".join(segments), parts.query, ""))


def duplicate_hints(rows: Iterable[dict]) -> List[dict]:
    material = list(rows)
    exact_groups: Dict[str, List[str]] = defaultdict(list)
    mirror_groups: Dict[str, List[str]] = defaultdict(list)
    for row in material:
        identifier = row.get("content_id", "")
        url = row.get("canonical_url") or row.get("item_url", "")
        canonical = canonicalize_url(url)
        if identifier and canonical:
            exact_groups[canonical].append(identifier)
            mirror_groups[_mirror_url_key(canonical)].append(identifier)

    hints = []
    exact_pairs = set()
    for canonical, identifiers in exact_groups.items():
        unique = sorted(set(identifiers))
        if len(unique) > 1:
            pair = tuple(unique)
            exact_pairs.add(pair)
            hints.append({"content_ids": unique, "reason": "canonical_url", "match_key": canonical})
    for mirror, identifiers in mirror_groups.items():
        unique = sorted(set(identifiers))
        if len(unique) > 1 and tuple(unique) not in exact_pairs:
            hints.append({"content_ids": unique, "reason": "language_mirror_url", "match_key": mirror})
    return hints
