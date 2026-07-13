# Exercises the real "Quick start" multi-stage build pattern from README.md:
# build pillowcase as a builder stage via `RUN ["/entrypoint.sh"]` (docker build
# never invokes ENTRYPOINT/CMD, so a build-time RUN is what actually runs
# pillowcase), then copy the produced /output into a final stage.
#
# Build context for this file is tests/ (so image.jpg and pillowcase.yml are
# reachable). The base image is `pillowcase:smoke`, built separately by
# run.sh from the repo root.

FROM pillowcase:smoke AS pillowcase
COPY image.jpg /input/photo.jpg
COPY pillowcase.yml /config/pillowcase.yml
ENV PILLOWCASE_QUALITY=40
RUN ["/entrypoint.sh"]

FROM python:3.12-slim AS output
RUN pip install --no-cache-dir ascii_magic
COPY --from=pillowcase /output /out
CMD ["python3", "-c", "import glob; from ascii_magic import AsciiArt; AsciiArt.from_image(glob.glob('/out/**/*.jpg', recursive=True)[0]).to_terminal()"]
