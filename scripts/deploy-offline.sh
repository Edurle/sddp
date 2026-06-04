#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: $0 <deploy-tar.gz>"
    exit 1
fi

ARCHIVE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"

if [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: File not found: $ARCHIVE"
    exit 1
fi

echo "=== SDD Deploy ==="
echo "Project: $PROJECT_DIR"
echo "Archive: $ARCHIVE"

BACKUP_DIR="$PROJECT_DIR/.deploy-backups/$(date +%Y%m%d_%H%M%S)"

for dir in backend/app frontend/src; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        echo "Backing up $dir -> ${dir##*/}.bak"
        mkdir -p "$BACKUP_DIR/${dir%/*}"
        mv "$PROJECT_DIR/$dir" "$BACKUP_DIR/$dir"
    fi
done

for f in backend/requirements.txt frontend/package.json frontend/package-lock.json; do
    if [ -f "$PROJECT_DIR/$f" ]; then
        mkdir -p "$BACKUP_DIR/${f%/*}"
        cp "$PROJECT_DIR/$f" "$BACKUP_DIR/$f"
    fi
done

tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

tar -xzf "$ARCHIVE" -C "$tmpdir"

echo "Deploying files..."
cp -r "$tmpdir/backend/app" "$PROJECT_DIR/backend/app"
cp "$tmpdir/backend/requirements.txt" "$PROJECT_DIR/backend/requirements.txt"
cp -r "$tmpdir/frontend/src" "$PROJECT_DIR/frontend/src"
cp "$tmpdir/frontend/package.json" "$PROJECT_DIR/frontend/package.json"
[ -f "$tmpdir/frontend/package-lock.json" ] && cp "$tmpdir/frontend/package-lock.json" "$PROJECT_DIR/frontend/package-lock.json"

echo "Rebuilding and restarting Docker services..."
cd "$PROJECT_DIR/docker"
docker compose down
docker compose up --build -d

echo ""
echo "=== Deploy Complete ==="
echo "Backups saved to: $BACKUP_DIR"
