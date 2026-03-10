#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/.run-logs"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
SIM_INTERSECTIONS="${SIM_INTERSECTIONS:-3}"
SIM_DURATION="${SIM_DURATION:-300}"
SIM_INJECT_EMERGENCY="${SIM_INJECT_EMERGENCY:-120}"
START_FRONTEND="${START_FRONTEND:-true}"
PIDS=()
PYTHON_BIN="${PYTHON_BIN:-}"

find_python() {
  if [ -n "$PYTHON_BIN" ] && command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "$PYTHON_BIN"
    return 0
  fi
  if command -v python3.11 >/dev/null 2>&1; then
    echo "python3.11"
    return 0
  fi
  if command -v python3.10 >/dev/null 2>&1; then
    echo "python3.10"
    return 0
  fi
  return 1
}

cleanup() {
  local pid
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT INT TERM

mkdir -p "$LOG_DIR"

if ! SELECTED_PYTHON="$(find_python)"; then
  echo "UrbanMind requires Python 3.11.x for the pinned ML dependencies."
  echo "Install python3.11 and rerun, or pass PYTHON_BIN=/path/to/python3.11 ./run_all.sh"
  exit 1
fi

if [ -d "$VENV_DIR" ]; then
  EXISTING_VERSION="$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
  if [ "$EXISTING_VERSION" != "3.11" ]; then
    rm -rf "$VENV_DIR"
  fi
fi

if [ ! -d "$VENV_DIR" ]; then
  "$SELECTED_PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

ACTIVE_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [ "$ACTIVE_VERSION" != "3.11" ]; then
  echo "Resolved virtualenv Python is $ACTIVE_VERSION, but UrbanMind requires 3.11."
  echo "Set PYTHON_BIN explicitly, for example:"
  echo "  PYTHON_BIN=$(command -v python3.11) ./run_all.sh"
  exit 1
fi

python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install -r "$ROOT_DIR/backend/requirements.txt" -r "$ROOT_DIR/edge/requirements.txt" pytest rich >/dev/null

if command -v docker >/dev/null 2>&1; then
  (cd "$ROOT_DIR" && docker compose up -d redis mqtt >/dev/null)
else
  echo "docker not found; skipping redis/mqtt startup"
fi

(
  cd "$ROOT_DIR"
  python3 -m uvicorn backend.main:app --host 0.0.0.0 --port "$BACKEND_PORT"
) >"$LOG_DIR/backend.log" 2>&1 &
PIDS+=("$!")

if [ "$START_FRONTEND" = "true" ]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found; skipping frontend startup"
  else
    (
      cd "$ROOT_DIR/frontend"
      if [ ! -d node_modules ]; then
        npm install >/dev/null
      fi
      npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
    ) >"$LOG_DIR/frontend.log" 2>&1 &
    PIDS+=("$!")
  fi
fi

(
  cd "$ROOT_DIR"
  python3 simulation/run_sim.py \
    --intersections "$SIM_INTERSECTIONS" \
    --duration "$SIM_DURATION" \
    --inject-emergency "$SIM_INJECT_EMERGENCY" \
    --backend-url "http://127.0.0.1:$BACKEND_PORT/intersections"
) >"$LOG_DIR/simulation.log" 2>&1 &
PIDS+=("$!")

cat <<EOF
UrbanMind is starting.

Backend:   http://localhost:$BACKEND_PORT
Frontend:  http://localhost:$FRONTEND_PORT
Logs:      $LOG_DIR

Tail logs:
  tail -f "$LOG_DIR/backend.log"
  tail -f "$LOG_DIR/frontend.log"
  tail -f "$LOG_DIR/simulation.log"

Press Ctrl+C to stop everything.
EOF

wait "${PIDS[@]}"
