from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

from .errors import ConfigError
from .profiles import Profile, PROFILE_KEYS

@dataclass
class Settings:
    input: Path
    output: Path
    config_path: Path
    quality: int
    strip_metadata: bool
    reencode: bool
    resize: bool
    convert: bool
    continue_on_error: bool

def load_settings(env: Mapping[str, str]) -> Settings:
    return Settings(
        input=Path(env.get("PILLOWCASE_INPUT", "/input")),
        output=Path(env.get("PILLOWCASE_OUTPUT", "/output")),
        config_path=Path(env.get("PILLOWCASE_CONFIG", "/config/pillowcase.yml")),
        quality=int(env.get("PILLOWCASE_QUALITY", "82")),
        strip_metadata=env.get("PILLOWCASE_STRIP_METADATA", "false").strip().lower() == "true",
        reencode=env.get("PILLOWCASE_REENCODE", "true").strip().lower() == "true",
        resize=env.get("PILLOWCASE_RESIZE", "true").strip().lower() == "true",
        convert=env.get("PILLOWCASE_CONVERT", "true").strip().lower() == "true",
        continue_on_error=env.get("PILLOWCASE_CONTINUE_ON_ERROR", "false").strip().lower() == "true",
    )


def load_profiles(path: Path) -> list[Profile]:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"could not parse {path}: {e}")
    if not isinstance(data, dict):
        raise ConfigError(
            f"pillowcase.yml must be a mapping with a top-level 'profiles' key, "
            f"got {type(data).__name__}"
        )
    raw_profiles = data.get("profiles", [])
    if not isinstance(raw_profiles, list):
        raise ConfigError("'profiles' must be a list")
    result = []
    for i, entry in enumerate(raw_profiles):
        if not isinstance(entry, dict):
            raise ConfigError(f"profile #{i + 1} must be a mapping")
        unknown = set(entry) - PROFILE_KEYS
        if unknown:
            raise ConfigError(f"profile #{i + 1} has unknown keys: {sorted(unknown)}")
        if "match" not in entry:
            raise ConfigError(f"profile #{i + 1} is missing required 'match'")
        result.append(Profile(**entry))
    return result
