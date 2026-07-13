import shutil
import sys
from pathlib import Path

from .config import Settings
from .errors import ConfigError, ProcessingError
from .pipeline import process_image
from .profiles import Profile, match_profile, resolve

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif",
              ".gif", ".bmp", ".tif", ".tiff"}


def _is_passthrough(eff) -> bool:
    """reencode disabled, single original width, single original format, no metadata stripping."""
    return (not eff.reencode
            and eff.widths == ["original"]
            and eff.formats == ["original"]
            and not eff.strip_metadata)


def run(settings: Settings, profiles: list[Profile]) -> int:
    processed = written = skipped = failed = 0
    input_root = settings.input
    written_paths: set[Path] = set()

    files = sorted(p for p in input_root.rglob("*") if p.is_file())
    for src in files:
        if src.suffix.lower() not in IMAGE_EXTS:
            skipped += 1
            continue

        rel = src.relative_to(input_root)
        eff = resolve(settings, match_profile(rel.as_posix(), profiles))
        dest_dir = settings.output / rel.parent

        if _is_passthrough(eff):
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            if dest in written_paths:
                raise ConfigError(
                    f"{src}: output path {dest} collides with a file already "
                    "written by this run (either an earlier source file, or "
                    "another width/format of this same file)"
                )
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)
            written_paths.add(dest)
            outputs = [dest]
        else:
            try:
                outputs = process_image(src, eff, dest_dir, written_paths)
            except ProcessingError as e:
                failed += 1
                if settings.continue_on_error:
                    print(f"warning: skipping {src}: {e}", file=sys.stderr)
                    continue
                print(f"error: {e}", file=sys.stderr)
                print(f"pillowcase: processed={processed} written={written} "
                      f"skipped={skipped} failed={failed}")
                return 1

        processed += 1
        written += len(outputs)

    print(f"pillowcase: processed={processed} written={written} "
          f"skipped={skipped} failed={failed}")
    return 0
