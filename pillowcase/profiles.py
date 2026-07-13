from dataclasses import dataclass, fields
from fnmatch import fnmatch


@dataclass
class Profile:
    match: str
    quality: int | None = None
    widths: list | None = None
    formats: list | None = None
    filename: str | None = None
    strip_metadata: bool | None = None
    reencode: bool | None = None
    resize: bool | None = None
    convert: bool | None = None


@dataclass
class EffectiveProfile:
    quality: int
    widths: list
    formats: list
    filename: str
    strip_metadata: bool
    reencode: bool


PROFILE_KEYS = {f.name for f in fields(Profile)}


def match_profile(rel_path: str, profiles: list[Profile]) -> Profile | None:
    for profile in profiles:
        if fnmatch(rel_path, profile.match):
            return profile
    return None


def _pick(profile, attr, default):
    if profile is not None and getattr(profile, attr) is not None:
        return getattr(profile, attr)
    return default


def resolve(settings, profile: Profile | None) -> EffectiveProfile:
    quality = _pick(profile, "quality", settings.quality)
    strip = _pick(profile, "strip_metadata", settings.strip_metadata)
    reencode = _pick(profile, "reencode", settings.reencode)
    resize_on = _pick(profile, "resize", settings.resize)
    convert_on = _pick(profile, "convert", settings.convert)

    widths = _pick(profile, "widths", ["original"])
    if not resize_on:
        widths = ["original"]
    formats = _pick(profile, "formats", ["original"])
    if not convert_on:
        formats = ["original"]
    filename = _pick(profile, "filename", "{stem}{width_suffix}.{ext}")

    return EffectiveProfile(
        quality=quality,
        widths=list(widths),
        formats=list(formats),
        filename=filename,
        strip_metadata=strip,
        reencode=reencode,
    )
