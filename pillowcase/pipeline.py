from pathlib import Path

from PIL import Image

try:  # register AVIF support if the plugin is installed
    import pillow_avif  # noqa: F401
except ImportError:
    pass

from .errors import ConfigError, ProcessingError
from .profiles import EffectiveProfile

Image.init()
def _get_extension(ext: str) -> str | None:
    return Image.registered_extensions().get(f".{ext}")


def _save_kwargs(pil_format: str, quality: int) -> dict:
    if pil_format in ("JPEG", "WEBP", "AVIF"):
        kw = {"quality": quality}
        if pil_format == "JPEG":
            kw["optimize"] = True
        if pil_format == "WEBP":
            kw["method"] = 6
        return kw
    if pil_format == "PNG":
        return {"optimize": True}
    return {}


def process_image(src: Path, eff: EffectiveProfile, dest_dir: Path,
                   written_paths: set[Path] | None = None) -> list[Path]:
    if written_paths is None:
        written_paths = set()
    try:
        with Image.open(src) as opened:
            opened.load()
            img = opened.copy()
    except Exception as e:
        raise ProcessingError(f"{src}: cannot open ({e})")

    src_ext = src.suffix.lstrip(".").lower()
    source_width = img.width
    source_height = img.height
    stem = src.stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for w in eff.widths:
        is_original = (w == "original")
        target_w = source_width if is_original else int(w)
        target_h = source_height if target_w == source_width \
            else max(1, round(source_height * target_w / source_width))
        for fmt in eff.formats:
            out_ext = src_ext if fmt == "original" else str(fmt).lower()
            pil_format = _get_extension(out_ext)
            if pil_format is None:
                raise ProcessingError(f"{src}: unsupported output format {out_ext!r}")

            width_suffix = "" if is_original else f"-{target_h}x{target_w}"
            values = {"stem": stem, "ext": out_ext, "width": target_w, "height": target_h,
                    "width_suffix": width_suffix}
            try:
                name = eff.filename.format(**values)
            except (KeyError, IndexError) as e:
                raise ConfigError(f"unknown token in filename template {eff.filename!r}: {e}")

            out_path = dest_dir / name
            if out_path in written_paths:
                raise ConfigError(
                    f"{src}: output path {out_path} collides with a file already "
                    "written by this run (either an earlier source file, or "
                    "another width/format of this same file)"
                )
            written_paths.add(out_path)

            try:
                frame = img
                if target_w != source_width:
                    frame = img.resize((target_w, target_h))

                # Strip metadata if requested by clearing frame.info before save
                if eff.strip_metadata:
                    frame.info = {}
                    kwargs = _save_kwargs(pil_format, eff.quality)
                else:
                    # Preserve metadata by passing it in kwargs
                    kwargs = _save_kwargs(pil_format, eff.quality)
                    if "exif" in img.info:
                        kwargs["exif"] = img.info["exif"]
                    if "icc_profile" in img.info:
                        kwargs["icc_profile"] = img.info["icc_profile"]

                try:
                    frame.save(out_path, format=pil_format, **kwargs)
                except OSError:
                    # Format can't save this mode (e.g. JPEG + RGBA/P) — retry as RGB.
                    if frame.mode in ("RGB", "L"):
                        raise
                    frame.convert("RGB").save(out_path, format=pil_format, **kwargs)
                written.append(out_path)
            except ProcessingError:
                # Re-raise ProcessingErrors that already come from nested calls
                raise
            except Exception as e:
                raise ProcessingError(
                    f"{src}: cannot process (width={target_w}, format={pil_format}): {e}"
                )

    return written
