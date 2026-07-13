#!/bin/sh
set -e
chown pillow:pillow /output /config 2>/dev/null || true
exec python -m pillowcase "$@"
