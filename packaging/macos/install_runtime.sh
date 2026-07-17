#!/bin/bash

set -euo pipefail

SOURCE_ROOT=""
PYTHON_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    --python)
      PYTHON_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$SOURCE_ROOT/hedgehog.py" || ! -f "$SOURCE_ROOT/VERSION" ]]; then
  echo "A valid --source-root is required." >&2
  exit 2
fi

VERSION="$(<"$SOURCE_ROOT/VERSION")"
APP_SUPPORT="$HOME/Library/Application Support/Hedgehog Master"
RUNTIME_DIR="$APP_SUPPORT/runtime-$VERSION"
PROJECT_ROOT="$RUNTIME_DIR/hedgehog_master"
PROJECTS_DIR="$APP_SUPPORT/projects"

mkdir -p "$PROJECT_ROOT" "$PROJECTS_DIR"
rsync -a --delete "$SOURCE_ROOT/" "$PROJECT_ROOT/" \
  --exclude '/.git/' \
  --exclude '/.venv/' \
  --exclude '/dist/' \
  --exclude '/examples/' \
  --exclude '/projects/' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '*.log'

if ! find "$PROJECTS_DIR" -mindepth 2 -name project.json -print -quit | grep -q .; then
  rsync -a "$SOURCE_ROOT/projects/" "$PROJECTS_DIR/" \
    --exclude '.DS_Store' \
    --exclude '__pycache__/' 2>/dev/null || true
fi

rm -rf "$PROJECT_ROOT/projects"
ln -s "$PROJECTS_DIR" "$PROJECT_ROOT/projects"
printf '%s\n' "$PROJECT_ROOT" > "$APP_SUPPORT/current-runtime"

if [[ -n "$PYTHON_PATH" && -x "$PYTHON_PATH" ]]; then
  BASE_PYTHON="$PYTHON_PATH"
else
  BASE_PYTHON="$(command -v python3 || true)"
fi

if [[ ! -x "$BASE_PYTHON" ]]; then
  echo "Python 3.11 or newer is required." >&2
  exit 1
fi

VENV_PYTHON="$RUNTIME_DIR/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
  "$BASE_PYTHON" -m venv "$RUNTIME_DIR/.venv"
fi
if ! "$VENV_PYTHON" -c 'import fitz, jsonschema, pptx' >/dev/null 2>&1; then
  echo "Installing Hedgehog Master Python dependencies..." >&2
  "$VENV_PYTHON" -m pip install --quiet --upgrade pip >&2
  "$VENV_PYTHON" -m pip install --quiet -r "$PROJECT_ROOT/requirements.txt" >&2
fi

printf '%s\n' "$VENV_PYTHON" > "$APP_SUPPORT/current-python"

echo "$PROJECT_ROOT"
