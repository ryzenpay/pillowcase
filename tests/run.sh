#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMG="pillowcase:smoke"
MULTISTAGE_IMG="pillowcase-multistage-smoke:smoke"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# `wc -c` reports file size portably across GNU/BSD/uutils coreutils,
# unlike `stat`, whose flags differ across those implementations.
filesize() {
  wc -c < "$1" | tr -d ' '
}

before_size="$(filesize "$REPO_ROOT/tests/image.jpg")"

docker build -t "$IMG" "$REPO_ROOT" --no-cache
docker build -f "$REPO_ROOT/tests/Dockerfile" -t "$MULTISTAGE_IMG" --target output "$REPO_ROOT/tests"

docker run --rm "$MULTISTAGE_IMG"

# The image CMD prints ASCII art to the terminal rather than raw bytes, so to
# check the actual output size we pull the produced file out of a container
# via `docker cp` instead of the container's stdout.
cid="$(docker create "$MULTISTAGE_IMG")"
docker cp "$cid:/out" "$WORK/out"
docker rm "$cid" > /dev/null

out_jpg="$(find "$WORK/out" -name '*.jpg' | head -n1)"
test -n "$out_jpg" || { echo "FAIL: multistage output missing/empty"; exit 1; }

after_size="$(filesize "$out_jpg")"

if [ "$after_size" -ge "$before_size" ]; then
  echo "FAIL: expected after < before (before=$before_size after=$after_size)"
  exit 1
fi

echo "MULTISTAGE BUILD-STAGE SMOKE OK (before=$before_size after=$after_size)"
