from pathlib import Path
from typing import Dict, Optional

import yaml


class ConfigError(ValueError):
    """Raised when a country configuration is incomplete or ambiguous."""


ALLOWED_TOP_LEVEL = {
    "version",
    "identity",
    "languages",
    "geography",
    "audiences",
    "task_families",
    "products",
    "channels",
    "access",
    "research",
    "regional_mappings",
}

REQUIRED_TOP_LEVEL = ALLOWED_TOP_LEVEL - {"version"}
ALLOWED_CHANNEL_SCOPES = {
    "country_candidate",
    "global_technical",
    "global_unknown",
    "migration_corridor",
    "recruitment_only",
}


def _require_mapping(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be a mapping")
    return value


def _require_nonempty_list(parent: dict, key: str) -> list:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{key} must be a non-empty list")
    return value


def validate_country_config(config: dict, expected_iso2: Optional[str] = None) -> dict:
    if not isinstance(config, dict):
        raise ConfigError("country config must be a mapping")
    unknown = set(config) - ALLOWED_TOP_LEVEL
    missing = REQUIRED_TOP_LEVEL - set(config)
    if unknown:
        raise ConfigError(f"unknown top-level fields: {', '.join(sorted(unknown))}")
    if missing:
        raise ConfigError(f"missing top-level fields: {', '.join(sorted(missing))}")

    identity = _require_mapping(config, "identity")
    iso2 = str(identity.get("iso2", "")).upper()
    iso3 = str(identity.get("iso3", "")).upper()
    if len(iso2) != 2 or not iso2.isalpha():
        raise ConfigError("identity.iso2 must be a two-letter code")
    if len(iso3) != 3 or not iso3.isalpha():
        raise ConfigError("identity.iso3 must be a three-letter code")
    if expected_iso2 and iso2 != expected_iso2.upper():
        raise ConfigError(f"config code {iso2} does not match filename {expected_iso2}")
    for field in ("name_en", "name_cn", "currency", "timezones"):
        if not identity.get(field):
            raise ConfigError(f"identity.{field} is required")

    languages = _require_mapping(config, "languages")
    _require_nonempty_list(languages, "core")
    languages.setdefault("exploratory", [])
    languages.setdefault("migration_corridor", [])

    geography = _require_mapping(config, "geography")
    _require_nonempty_list(geography, "country_anchors")
    if not isinstance(geography.get("admin1", []), list):
        raise ConfigError("geography.admin1 must be a list")
    if "allow_unknown_admin1" not in geography:
        raise ConfigError("geography.allow_unknown_admin1 is required")

    audiences = _require_mapping(config, "audiences")
    if len(_require_nonempty_list(audiences, "mainstream_roles")) < 3:
        raise ConfigError("at least three mainstream roles are required")
    _require_nonempty_list(audiences, "technical_supplement")
    if len(_require_nonempty_list(config, "task_families")) < 4:
        raise ConfigError("at least four task families are required")

    products = _require_mapping(config, "products")
    _require_nonempty_list(products, "direct")
    _require_nonempty_list(products, "adjacent")

    channels = _require_nonempty_list(config, "channels")
    names = set()
    for index, channel in enumerate(channels):
        if not isinstance(channel, dict):
            raise ConfigError(f"channels[{index}] must be a mapping")
        for field in (
            "name", "family", "status", "scope_default", "candidate_streams",
            "access_mode", "audience_bias", "url", "seed_reason",
        ):
            if field not in channel or channel[field] in (None, ""):
                raise ConfigError(f"channels[{index}].{field} is required")
        if channel["name"] in names:
            raise ConfigError(f"duplicate channel name: {channel['name']}")
        names.add(channel["name"])
        if channel["status"] != "Candidate":
            raise ConfigError(f"channel {channel['name']} must begin as Candidate")
        if channel["scope_default"] not in ALLOWED_CHANNEL_SCOPES:
            raise ConfigError(f"invalid channel scope: {channel['scope_default']}")
        if not set(channel["candidate_streams"]).issubset({"A", "B", "C"}):
            raise ConfigError(f"invalid evidence stream for {channel['name']}")

    access = _require_mapping(config, "access")
    _require_nonempty_list(access, "anonymous_public_path")
    access.setdefault("auth_optional", [])
    access.setdefault("consent_required", [])
    access.setdefault("prohibited", [])

    research = _require_mapping(config, "research")
    for field in (
        "window_start", "window_end", "pilot_results_per_channel",
        "saturation_batches", "review_sample_rate", "required_mainstream_roles",
        "required_task_families", "required_source_families",
    ):
        if field not in research:
            raise ConfigError(f"research.{field} is required")

    regional_mappings = _require_mapping(config, "regional_mappings")
    _require_nonempty_list(regional_mappings, "regions")
    _require_nonempty_list(regional_mappings, "language_zones")
    regional_mappings.setdefault("migration_corridors", [])
    return config


def load_country_config(config_root: Path, iso2: str) -> dict:
    code = iso2.upper()
    path = Path(config_root) / "countries" / f"{code}.yml"
    if not path.exists():
        raise ConfigError(f"country config not found: {code}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ConfigError(f"invalid YAML in {path.name}: {error}") from error
    return validate_country_config(data, expected_iso2=code)


def load_all_country_configs(config_root: Path) -> Dict[str, dict]:
    country_dir = Path(config_root) / "countries"
    configs = {}
    for path in sorted(country_dir.glob("*.yml")):
        code = path.stem.upper()
        configs[code] = load_country_config(config_root, code)
    if not configs:
        raise ConfigError(f"no country configs found in {country_dir}")
    iso3_codes = [item["identity"]["iso3"] for item in configs.values()]
    if len(iso3_codes) != len(set(iso3_codes)):
        raise ConfigError("duplicate ISO3 codes across country configs")
    return configs
