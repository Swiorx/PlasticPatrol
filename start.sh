#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$REPO_ROOT/backend"
FRONTEND="$REPO_ROOT/frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[start]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $*"; }
die()  { echo -e "${RED}[error]${NC} $*"; exit 1; }

cleanup() {
    log "Shutting down..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    log "Done."
}
trap cleanup EXIT INT TERM

# ── 1. PostgreSQL ────────────────────────────────────────────────────────────
log "Starting PostgreSQL..."
if ! pg_isready -q 2>/dev/null; then
    sudo service postgresql start
    for i in $(seq 1 10); do
        pg_isready -q 2>/dev/null && break
        sleep 1
    done
    pg_isready -q || die "PostgreSQL did not start in time."
fi
log "PostgreSQL is ready."

# ── 2. Ensure DB + PostGIS exist ─────────────────────────────────────────────
if ! sudo -u postgres psql -lqt 2>/dev/null | cut -d'|' -f1 | grep -qw plasticpatrol; then
    warn "Database 'plasticpatrol' not found — creating it..."
    sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'admin123';" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE plasticpatrol OWNER admin;"
    sudo -u postgres psql -d plasticpatrol -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    log "Database created."
fi

# ── 3. Backend venv ──────────────────────────────────────────────────────────
if [ ! -f "$BACKEND/.venv/bin/activate" ]; then
    log "Creating Python virtual environment..."
    python3 -m venv "$BACKEND/.venv"
fi

log "Installing/verifying backend dependencies..."
"$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"

# ── 4. Start backend ─────────────────────────────────────────────────────────
log "Starting backend on http://localhost:8000 ..."
cd "$BACKEND"
"$BACKEND/.venv/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait until backend is accepting connections
for i in $(seq 1 20); do
    curl -sf http://localhost:8000/api/health > /dev/null 2>&1 && break
    sleep 1
done
curl -sf http://localhost:8000/api/health > /dev/null 2>&1 || warn "Backend health check failed — check logs above."
log "Backend is up (PID $BACKEND_PID)."

# ── 5. Frontend ───────────────────────────────────────────────────────────────
if [ ! -d "$FRONTEND/node_modules" ]; then
    log "Installing frontend dependencies (npm install)..."
    cd "$FRONTEND" && npm install
fi

log "Starting frontend on http://localhost:4200 ..."
cd "$FRONTEND"
npm start &
FRONTEND_PID=$!

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  Frontend  →  http://localhost:4200"
log "  Backend   →  http://localhost:8000"
log "  API docs  →  http://localhost:8000/docs"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Press Ctrl+C to stop everything."

wait
