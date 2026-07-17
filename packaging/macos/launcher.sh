#!/bin/bash

set -u

CONTENTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE_DIR="$(cd "$CONTENTS_DIR/.." && pwd)"
PACKAGE_DIR="$(cd "$BUNDLE_DIR/.." && pwd)"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
APP_SUPPORT="$HOME/Library/Application Support/Hedgehog Master"
LOG_DIR="$HOME/Library/Logs/Hedgehog Master"
PORT="${HEDGEHOG_MASTER_PORT:-4174}"

mkdir -p "$APP_SUPPORT" "$LOG_DIR"
EXPECTED_VERSION="$(/bin/cat "$RESOURCES_DIR/version" 2>/dev/null || echo dev)"

notify() {
  /usr/bin/osascript -e "display notification \"$1\" with title \"Hedgehog Master\"" >/dev/null 2>&1 || true
}

show_error() {
  /usr/bin/osascript -e "display alert \"Hedgehog Master\" message \"$1\" as critical" >/dev/null 2>&1 || true
}

PROJECT_ROOT=""
if [[ -f "$RESOURCES_DIR/runtime-root" ]]; then
  PROJECT_ROOT="$(/bin/cat "$RESOURCES_DIR/runtime-root")"
elif [[ -f "$APP_SUPPORT/current-runtime" ]]; then
  PROJECT_ROOT="$(/bin/cat "$APP_SUPPORT/current-runtime")"
fi

if [[ "$(/bin/cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo missing)" != "$EXPECTED_VERSION" ]]; then
  PROJECT_ROOT=""
fi

if [[ ! -f "$PROJECT_ROOT/hedgehog.py" ]]; then
  if [[ -x "$PACKAGE_DIR/setup.command" ]]; then
    notify "First-run setup has opened in Terminal. The workbench will start when setup completes."
    /usr/bin/open -a Terminal "$PACKAGE_DIR/setup.command"
    exit 0
  fi
  show_error "The local runtime is not installed. Rebuild the desktop app or run setup.command from the delivery folder."
  exit 1
fi

URL="http://127.0.0.1:$PORT/"
STATUS="$(/usr/bin/curl -fsS "$URL/api/status" 2>/dev/null || true)"
if printf '%s' "$STATUS" | /usr/bin/grep -q '"repository": "hedgehog-master"' && \
  printf '%s' "$STATUS" | /usr/bin/grep -q "\"version\": \"$EXPECTED_VERSION\""; then
  /usr/bin/open "$URL"
  exit 0
fi

while /usr/sbin/lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; do
  PORT=$((PORT + 1))
  if [[ "$PORT" -gt 4194 ]]; then
    show_error "No available local port was found between 4174 and 4194."
    exit 1
  fi
done
URL="http://127.0.0.1:$PORT/"

PYTHON=""
if [[ -f "$RESOURCES_DIR/python-path" ]]; then
  PYTHON="$(/bin/cat "$RESOURCES_DIR/python-path")"
elif [[ -f "$APP_SUPPORT/current-python" ]]; then
  PYTHON="$(/bin/cat "$APP_SUPPORT/current-python")"
fi
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(cd "$PROJECT_ROOT/.." && pwd)/.venv/bin/python"
fi
if [[ ! -x "$PYTHON" ]]; then
  if [[ -x "$PACKAGE_DIR/setup.command" ]]; then
    notify "First-run setup has opened in Terminal. The workbench will start when setup completes."
    /usr/bin/open -a Terminal "$PACKAGE_DIR/setup.command"
    exit 0
  fi
  show_error "Python dependencies are not installed. Run setup.command from the delivery folder first."
  exit 1
fi

LOG_FILE="$LOG_DIR/workbench-$PORT.log"
cd "$PROJECT_ROOT" || exit 1
nohup "$PYTHON" hedgehog.py serve --port "$PORT" >>"$LOG_FILE" 2>&1 </dev/null &

for _ in {1..80}; do
  STATUS="$(/usr/bin/curl -fsS "$URL/api/status" 2>/dev/null || true)"
  if printf '%s' "$STATUS" | /usr/bin/grep -q '"repository": "hedgehog-master"' && \
    printf '%s' "$STATUS" | /usr/bin/grep -q "\"version\": \"$EXPECTED_VERSION\""; then
    /usr/bin/open "$URL"
    notify "Workbench started on port $PORT."
    exit 0
  fi
  /bin/sleep 0.25
done

show_error "The local workbench did not start. Review the log at $LOG_FILE."
exit 1
