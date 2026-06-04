#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

backend_pid() { cat "$PID_DIR/backend.pid" 2>/dev/null || echo ""; }
frontend_pid() { cat "$PID_DIR/frontend.pid" 2>/dev/null || echo ""; }

is_running() { pid=$1; [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; }

start_backend() {
    pid=$(backend_pid)
    if is_running "$pid"; then
        echo "Backend already running (PID $pid)"
        return 0
    fi
    echo "Starting backend..."
    cd "$BACKEND_DIR"
    rm -f test.db sdd.db
    nohup conda run -n sdd python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    sleep 2
    pid=$(backend_pid)
    if is_running "$pid"; then
        echo "Backend started (PID $pid) on http://localhost:8000"
    else
        echo "ERROR: Backend failed to start. See $LOG_DIR/backend.log"
        cat "$LOG_DIR/backend.log"
        return 1
    fi
}

start_frontend() {
    pid=$(frontend_pid)
    if is_running "$pid"; then
        echo "Frontend already running (PID $pid)"
        return 0
    fi
    echo "Starting frontend..."
    cd "$FRONTEND_DIR"
    nohup npx vite --port 5173 --host 0.0.0.0 \
        > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    sleep 3
    pid=$(frontend_pid)
    if is_running "$pid"; then
        echo "Frontend started (PID $pid) on http://localhost:5173"
    else
        echo "ERROR: Frontend failed to start. See $LOG_DIR/frontend.log"
        cat "$LOG_DIR/frontend.log"
        return 1
    fi
}

stop_backend() {
    pid=$(backend_pid)
    if is_running "$pid"; then
        echo "Stopping backend (PID $pid)..."
        kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
        sleep 1
    fi
    pids=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "Killing remaining processes on port 8000: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
    rm -f "$PID_DIR/backend.pid"
    echo "Backend stopped"
    rm -f "$BACKEND_DIR/test.db"
}

stop_frontend() {
    pid=$(frontend_pid)
    if is_running "$pid"; then
        echo "Stopping frontend (PID $pid)..."
        kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
        sleep 1
    fi
    pids=$(lsof -ti:5173 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "Killing remaining processes on port 5173: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
    rm -f "$PID_DIR/frontend.pid"
    echo "Frontend stopped"
}

stop_all() {
    stop_frontend
    stop_backend
}

start_all() {
    start_backend
    start_frontend
}

status() {
    bpid=$(backend_pid)
    fpid=$(frontend_pid)
    if is_running "$bpid"; then echo "Backend: running (PID $bpid)"; else echo "Backend: stopped"; fi
    if is_running "$fpid"; then echo "Frontend: running (PID $fpid)"; else echo "Frontend: stopped"; fi
}

run_e2e() {
    cd "$FRONTEND_DIR"
    npx playwright test "$@" 2>&1
}

case "${1:-help}" in
    start)       start_all ;;
    start-be)    start_backend ;;
    start-fe)    start_frontend ;;
    stop)        stop_all ;;
    stop-be)     stop_backend ;;
    stop-fe)     stop_frontend ;;
    restart)     stop_all; start_all ;;
    status)      status ;;
    e2e)         shift; run_e2e "$@" ;;
    logs-be)     tail -f "$LOG_DIR/backend.log" ;;
    logs-fe)     tail -f "$LOG_DIR/frontend.log" ;;
    help|*)
        echo "Usage: $0 {start|start-be|start-fe|stop|stop-be|stop-fe|restart|status|e2e|logs-be|logs-fe}"
        echo ""
        echo "  start       Start backend + frontend"
        echo "  start-be    Start backend only"
        echo "  start-fe    Start frontend only"
        echo "  stop        Stop all services"
        echo "  stop-be     Stop backend"
        echo "  stop-fe     Stop frontend"
        echo "  restart     Restart all services"
        echo "  status      Show service status"
        echo "  e2e [args]  Run E2E tests (args passed to playwright)"
        echo "  logs-be     Tail backend logs"
        echo "  logs-fe     Tail frontend logs"
        ;;
esac
