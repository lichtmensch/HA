#!/bin/sh

ROOT="/share/Container/clamav-modern"
DOCKER="/share/CACHEDEV1_DATA/.qpkg/container-station/bin/docker"
IMAGE="clamav/clamav:1.5.4_base-debian13-slim"
MODE="${1:-inbox}"
LOCK="$ROOT/control/.scan-lock"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$ROOT/logs/scan-$MODE-$STAMP.log"
STATUS="$ROOT/control/last-scan-status"

mkdir -p "$ROOT/logs" "$ROOT/quarantine" "$ROOT/control"
if ! mkdir "$LOCK" 2>/dev/null; then
    exit 0
fi

cleanup() {
    rmdir "$LOCK" 2>/dev/null
}
trap cleanup 0 1 2 15

"$ROOT/control/update.sh" || true

case "$MODE" in
    inbox)
        "$DOCKER" run --rm \
            --name clamav-scan-inbox \
            --cpus 1 \
            --memory 2g \
            --entrypoint clamscan \
            -v clamav_modern_db:/var/lib/clamav:ro \
            -v /share/CACHEDEV1_DATA/Download:/scan/Download:ro \
            -v /share/CACHEDEV1_DATA/Public:/scan/Public:ro \
            -v "$ROOT/quarantine:/quarantine" \
            "$IMAGE" -r --infected --copy=/quarantine \
            --max-filesize=100M --max-scansize=500M --max-recursion=25 \
            /scan/Download /scan/Public >"$LOG" 2>&1
        ;;
    homes)
        "$DOCKER" run --rm \
            --name clamav-scan-homes \
            --cpus 1 \
            --memory 2g \
            --entrypoint clamscan \
            -v clamav_modern_db:/var/lib/clamav:ro \
            -v /share/CACHEDEV1_DATA/homes:/scan/homes:ro \
            -v "$ROOT/quarantine:/quarantine" \
            "$IMAGE" -r --infected --copy=/quarantine \
            --exclude-dir='^/scan/homes/timo/movie($|/)' \
            --exclude-dir='/(\.snapshot|@Recycle|\.streams)($|/)' \
            --max-filesize=100M --max-scansize=500M --max-recursion=25 \
            /scan/homes >"$LOG" 2>&1
        ;;
    test)
        "$DOCKER" run --rm \
            --name clamav-scan-test \
            --cpus 1 \
            --memory 2g \
            --entrypoint clamscan \
            -v clamav_modern_db:/var/lib/clamav:ro \
            -v "$ROOT/test:/scan/test:ro" \
            "$IMAGE" -r /scan/test >"$LOG" 2>&1
        ;;
    *)
        echo "Unbekannter Scanmodus: $MODE" >&2
        exit 2
        ;;
esac
RC=$?

printf '%s mode=%s result=%s log=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$MODE" "$RC" "$LOG" >"$STATUS"
find "$ROOT/logs" -type f -name 'scan-*.log' -mtime +180 -delete 2>/dev/null
exit "$RC"
