# pillowcase

## What it is

pillowcase is a dockerized, pure-[Pillow](https://pillow.readthedocs.io/) image
processing tool for static asset pipelines. It runs as a builder stage in a
multi-stage Dockerfile: point it at a directory of source images, optionally
give it a `pillowcase.yml` config, and it compresses, resizes, converts, and/or
strips metadata from every image, mirroring the input directory structure into
an output directory. No native image libraries beyond Pillow (and the AVIF
plugin) are required — just Python and Pillow doing the work.

## Quick start

The primary use case is a multi-stage Docker build, where `pillowcase`
produces optimized assets that get copied into a final serving image:

```dockerfile
FROM ghcr.io/ryzenpay/pillowcase AS pillowcase
COPY ./raw-images /input
COPY ./pillowcase.yml /config/pillowcase.yml
ENV PILLOWCASE_QUALITY=80
RUN ["/entrypoint.sh"]

FROM nginx:alpine
COPY --from=pillowcase /output /usr/share/nginx/html/img
```

The `RUN` line is required: `docker build` never invokes `ENTRYPOINT`/`CMD`, only
`RUN` instructions execute during a build, so this is what actually makes
pillowcase process the copied images as part of the `assets` stage.

## Test locally

run `./tests/run.sh`

## Environment variables

| Variable                       | Default                    | Meaning                                                                 |
|---------------------------------|-----------------------------|--------------------------------------------------------------------------|
| `PILLOWCASE_INPUT`              | `/input`                   | Directory to read source images from.                                   |
| `PILLOWCASE_OUTPUT`             | `/output`                  | Directory to write processed images to.                                 |
| `PILLOWCASE_CONFIG`             | `/config/pillowcase.yml`   | Path to the YAML profile config file (optional; ignored if missing).    |
| `PILLOWCASE_QUALITY`            | `82`                       | Default encode quality, integer `1`-`100`.                              |
| `PILLOWCASE_STRIP_METADATA`     | `false`                    | Strip EXIF/ICC metadata from output images.                             |
| `PILLOWCASE_REENCODE`           | `true`                     | Re-encode images even if no resize/convert/strip is needed.             |
| `PILLOWCASE_RESIZE`             | `true`                     | Enable resizing (per-profile `widths`). When `false`, output is original width only. |
| `PILLOWCASE_CONVERT`            | `true`                     | Enable format conversion (per-profile `formats`). When `false`, output keeps the original format. |
| `PILLOWCASE_CONTINUE_ON_ERROR`  | `false`                    | On a per-file processing failure, log and continue instead of stopping. |


## Config file (`pillowcase.yml`)

The config file has a top-level `profiles` list. Each profile is matched
against each input file's path (relative to `PILLOWCASE_INPUT`) using shell
glob syntax (`fnmatch`), and the **first matching profile wins** — later
profiles are not consulted once a match is found. Files that match no profile
use the settings' global defaults.

| Key              | Type          | Default (when unset)                | Meaning                                              |
|------------------|---------------|--------------------------------------|-------------------------------------------------------|
| `match`          | string        | *(required)*                         | Glob pattern matched against the file's relative path. |
| `quality`        | int           | `PILLOWCASE_QUALITY`                 | Encode quality for this profile, `1`-`100`.           |
| `widths`         | list of int   | `["original"]`                       | Output widths to generate.                            |
| `formats`        | list of string| `["original"]`                       | Output formats to generate (e.g. `webp`, `jpg`, `original`). |
| `filename`       | string        | `"{stem}{width_suffix}.{ext}"`       | Filename template (see below).                        |
| `strip_metadata` | bool          | `PILLOWCASE_STRIP_METADATA`          | Strip EXIF/ICC metadata for this profile.              |
| `reencode`       | bool          | `PILLOWCASE_REENCODE`                | Force re-encode for this profile.                      |
| `resize`         | bool          | `PILLOWCASE_RESIZE`                  | Gate: enable/disable resizing for this profile.        |
| `convert`        | bool          | `PILLOWCASE_CONVERT`                 | Gate: enable/disable format conversion for this profile. |

**Gate semantics:** `resize` and `convert` are gates, checked before `widths`/
`formats` are applied. If `resize` resolves to `false`, `widths` collapses to
`["original"]` regardless of what the profile specifies. If `convert` resolves
to `false`, `formats` collapses to `["original"]` regardless of what the
profile specifies.

If none of `reencode`, `resize`/`widths`, `convert`/`formats`, or
`strip_metadata` end up doing anything for a file (re-encode disabled, single
original width, single original format, no metadata stripping), the file is
copied through byte-for-byte instead of being re-encoded by Pillow.

## Filename templates

The `filename` template is expanded per output file using these tokens:

| Token            | Meaning                                                             |
|------------------|------------------------------------------------------------------------|
| `{stem}`         | Source filename without extension.                                   |
| `{ext}`          | Output extension (e.g. `webp`, `jpg`).                                |
| `{width}`        | Output width in pixels.                                              |
| `{height}`       | Output height in pixels (preserving the source aspect ratio).        |
| `{width_suffix}` | `""` for the original width, `"-{height}x{width}"` for any other width. |

A template that would produce colliding filenames is rejected as a config
error: multiple `widths` require `{width}` or `{width_suffix}` in the
template (`{height}` alone doesn't count — two different widths could round
to the same height), and multiple `formats` require `{ext}`.

Note: the literal string `"original"` is a special sentinel value that can be
used as an entry inside `widths` (alongside explicit integer widths) to
request an un-suffixed, native-size output. Width matching against `widths`
entries is not based on the source image's actual pixel width — an integer
entry like `800` is always treated as an explicit target width and always
gets a `-{height}x{width}` suffix, even if the source image happens to be
800px wide.

Worked example — a 1200x900 `photo.jpg` with `widths: [400, "original"]`,
`formats: [webp, jpg]`, default `filename: "{stem}{width_suffix}.{ext}"`:

```
photo-300x400.webp
photo-300x400.jpg
photo.webp        # width_suffix is "" for the "original" entry
photo.jpg
```

## Examples

1. **WebP with original-format fallback** — convert everything to WebP but
also keep the original format as a fallback for browsers without WebP
support:

```yaml
profiles:
  - match: "*"
    formats: [webp, original]
```

2. **Responsive thumbnails** — generate multiple widths in WebP for a
`thumbnails/` directory, with a filename template that avoids collisions:

```yaml
profiles:
  - match: "thumbnails/*"
    quality: 65
    widths: [200, 400, 800]
    formats: [webp]
    filename: "{stem}-{width}w.{ext}"
```

## License

[MIT](LICENSE)