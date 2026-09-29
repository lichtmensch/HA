#!/bin/sh

CONTROL_DIR="/share/CACHEDEV1_DATA/.antivirus/control"
LOCK_DIR="$CONTROL_DIR/.daily-update.lock"
LOG_FILE="$CONTROL_DIR/daily-update.log"

mkdir -p "$CONTROL_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    exit 0
fi

cleanup() {
    rmdir "$LOCK_DIR" 2>/dev/null
}
trap cleanup 0 1 2 15

/usr/local/bin/freshclam -u admin --update-db=daily -l "$LOG_FILE"
exit $?
