#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== SDD Docker Deployment ==="

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "ERROR: .env file not found in $SCRIPT_DIR/"
    echo "Copy .env.example to .env and fill in your values:"
    echo "  cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    exit 1
fi

source "$SCRIPT_DIR/.env"

echo "[1/3] Building images..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" build

echo "[2/3] Starting services..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

echo "[3/3] Running database migrations..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec backend python -m alembic -c alembic.ini upgrade head

echo ""
echo "Creating admin account..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec backend python scripts/create_admin.py

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: http://localhost:80"
echo "Backend:  http://localhost:8000"
echo "Admin:    $ADMIN_EMAIL / (your password)"
echo ""
echo "Useful commands:"
echo "  docker compose -f $SCRIPT_DIR/docker-compose.yml logs -f"
echo "  docker compose -f $SCRIPT_DIR/docker-compose.yml restart backend"
echo "  docker compose -f $SCRIPT_DIR/docker-compose.yml down"
