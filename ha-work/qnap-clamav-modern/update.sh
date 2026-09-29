#!/bin/sh

ROOT="/share/Container/clamav-modern"
DOCKER="/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker"
IMAGE="clamav/clamav:1.5.4_base-debian13-slim"
LOCK="$ROOT/control/.update-lock"
LOG="$ROOT/logs/update-$(date +%Y%m%d-%H%M%S).log"

mkdir -p "$ROOT/logs" "$ROOT/control"
if ! mkdir "$LOCK" 2>/dev/null; then
    exit 0
fi

cleanup() {
    rmdir "$LOCK" 2>/dev/null
}
trap cleanup 0 1 2 15

"$DOCKER" run --rm \
    --name clamav-signature-update \
    --cpus 0.5 \
    --memory 1g \
    --entrypoint freshclam \
    -v clamav_modern_db:/var/lib/clamav \
    "$IMAGE" \
    --datadir=/var/lib/clamav \
    --stdout >"$LOG" 2>&1
RC=$?

find "$ROOT/logs" -type f -name 'update-*.log' -mtime +90 -delete 2>/dev/null
exit "$RC"
