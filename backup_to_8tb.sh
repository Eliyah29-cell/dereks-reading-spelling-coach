#!/bin/bash

set -Eeuo pipefail

PROJECT_FOLDER="/home/derek/PycharmProjects/PythonProject1"
DRIVE_UUID="75c9eeae-958c-4234-a97b-6779ea87125b"
BACKUP_ROOT_NAME="Dereks-Spelling-Coach-Project-Backup"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$HOME/.local/state/dereks-spelling-coach/backup.log"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    printf '%s | %s\n' \
        "$(date '+%Y-%m-%d %H:%M:%S')" \
        "$1" | tee -a "$LOG_FILE"
}

fail() {
    log "BACKUP FAILED: $1"
    exit 1
}

trap 'status=$?; log "BACKUP FAILED: unexpected error, exit code $status"; exit "$status"' ERR

echo "Checking the 8 TB drive..."

MOUNT_POINT="$(
    findmnt -rn -S "UUID=$DRIVE_UUID" -o TARGET |
    head -n 1 || true
)"

[[ -n "$MOUNT_POINT" ]] ||
    fail "The 8 TB drive is not mounted."

[[ -d "$MOUNT_POINT" ]] ||
    fail "The mount point does not exist: $MOUNT_POINT"

[[ -w "$MOUNT_POINT" ]] ||
    fail "The mount point is not writable: $MOUNT_POINT"

BACKUP_ROOT="$MOUNT_POINT/$BACKUP_ROOT_NAME"
BACKUP_FOLDER="$BACKUP_ROOT/backup-$TIMESTAMP"

mkdir -p "$BACKUP_FOLDER"

ITEMS=(
    "reading_spelling_coach.py"
    "build_word_bank.py"
    "config.txt"
    "data"
    "docs"
    "README.md"
    "LICENSE"
    "CONTRIBUTING.md"
    ".gitignore"
    "backup_to_8tb.sh"
)

echo "Copying project files..."

for item in "${ITEMS[@]}"; do
    SOURCE="$PROJECT_FOLDER/$item"

    [[ -e "$SOURCE" ]] ||
        fail "Required project item is missing: $item"

    cp -a "$SOURCE" "$BACKUP_FOLDER/"
done

echo "Verifying copied files..."

for item in "${ITEMS[@]}"; do
    [[ -e "$BACKUP_FOLDER/$item" ]] ||
        fail "Backup verification failed for: $item"
done

(
    cd "$BACKUP_FOLDER"

    find . \
        -type f \
        ! -name "SHA256SUMS.txt" \
        -print0 |
        sort -z |
        xargs -0 sha256sum > SHA256SUMS.txt

    sha256sum -c SHA256SUMS.txt >/dev/null
)

sync

trap - ERR

log "BACKUP SUCCESS: $BACKUP_FOLDER"

echo
echo "Backup verified successfully."
echo "Saved to:"
echo "$BACKUP_FOLDER"
