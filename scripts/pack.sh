#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="$PROJECT_DIR/sdd-deploy-${TIMESTAMP}.tar.gz"

echo "=== SDD Deploy Pack ==="
echo "Project: $PROJECT_DIR"

tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

mkdir -p "$tmpdir/backend/app" "$tmpdir/frontend/src"

cp -r "$PROJECT_DIR/backend/app/"* "$tmpdir/backend/app/"
cp "$PROJECT_DIR/backend/requirements.txt" "$tmpdir/backend/"

cp -r "$PROJECT_DIR/frontend/src/"* "$tmpdir/frontend/src/"
cp "$PROJECT_DIR/frontend/package.json" "$tmpdir/frontend/"
[ -f "$PROJECT_DIR/frontend/package-lock.json" ] && cp "$PROJECT_DIR/frontend/package-lock.json" "$tmpdir/frontend/"

find "$tmpdir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$tmpdir" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$tmpdir" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find "$tmpdir" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$tmpdir" -type f -name "*.db" -delete 2>/dev/null || true
find "$tmpdir" -type f -name ".env" -delete 2>/dev/null || true

tar -czf "$OUTPUT" -C "$tmpdir" .

SIZE=$(du -h "$OUTPUT" | cut -f1)
echo ""
echo "=== Pack Complete ==="
echo "Output: $OUTPUT  $SIZE"
