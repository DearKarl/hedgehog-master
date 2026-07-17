#!/bin/bash

set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_ROOT="$PACKAGE_DIR/hedgehog_master"
VERSION="$(<"$SOURCE_ROOT/VERSION")"
APP_SUPPORT="$HOME/Library/Application Support/Hedgehog Master"
RUNTIME_DIR="$APP_SUPPORT/runtime-$VERSION"
PROJECT_ROOT="$RUNTIME_DIR/hedgehog_master"
PROJECTS_DIR="$APP_SUPPORT/projects"

echo "Hedgehog Master local setup / 本地安装"
echo "===================================="

PYTHON_BIN="${HEDGEHOG_PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' 2>/dev/null; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python 3.11 or newer is required. / 需要 Python 3.11 或更高版本。"
  read -r -p "Press Enter to close..."
  exit 1
fi

mkdir -p "$PROJECT_ROOT" "$PROJECTS_DIR"
rsync -a --delete "$SOURCE_ROOT/" "$PROJECT_ROOT/" \
  --exclude '/.venv/' \
  --exclude '/projects/' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '*.log'
rm -rf "$PROJECT_ROOT/projects"
ln -s "$PROJECTS_DIR" "$PROJECT_ROOT/projects"
printf '%s\n' "$PROJECT_ROOT" > "$APP_SUPPORT/current-runtime"

"$PYTHON_BIN" -m venv "$RUNTIME_DIR/.venv"
"$RUNTIME_DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$RUNTIME_DIR/.venv/bin/python" -m pip install --quiet -r "$PROJECT_ROOT/requirements.txt"
printf '%s\n' "$RUNTIME_DIR/.venv/bin/python" > "$APP_SUPPORT/current-python"

if ! command -v node >/dev/null 2>&1; then
  echo "Warning: Node.js 20+ is required for diagram compilation."
  echo "提示：流程图编译需要 Node.js 20 或更高版本。"
fi

echo
echo "Setup complete. Opening Hedgehog Master... / 安装完成，正在打开工作台……"
open "$PACKAGE_DIR/Hedgehog Master.app"
