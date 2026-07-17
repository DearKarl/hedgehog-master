#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION="$(<"$REPO_ROOT/VERSION")"
DIST_ROOT="$REPO_ROOT/dist"
PACKAGE_NAME="Hedgehog-Master-$VERSION-macos"
PACKAGE_DIR="$DIST_ROOT/$PACKAGE_NAME"
PROJECT_DIR="$PACKAGE_DIR/hedgehog_master"
ZIP_PATH="$DIST_ROOT/$PACKAGE_NAME.zip"

rm -rf "$PACKAGE_DIR" "$ZIP_PATH"
mkdir -p "$PROJECT_DIR"

rsync -a "$REPO_ROOT/" "$PROJECT_DIR/" \
  --exclude '/.git/' \
  --exclude '/.venv/' \
  --exclude '/dist/' \
  --exclude '/examples/' \
  --exclude '/projects/*' \
  --exclude 'node_modules/' \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '*.log'

mkdir -p "$PROJECT_DIR/projects"
if [[ -f "$REPO_ROOT/projects/README.md" ]]; then
  cp "$REPO_ROOT/projects/README.md" "$PROJECT_DIR/projects/README.md"
fi

sed "s/__VERSION__/$VERSION/g" "$SCRIPT_DIR/START_HERE.md" > "$PACKAGE_DIR/START_HERE.md"
cp "$SCRIPT_DIR/setup.command" "$PACKAGE_DIR/setup.command"
chmod +x "$PACKAGE_DIR/setup.command"

"$REPO_ROOT/packaging/macos/build_app.sh" \
  --output "$PACKAGE_DIR/Hedgehog Master.app"

(
  cd "$PACKAGE_DIR"
  find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 shasum -a 256 > MANIFEST.sha256
)

ditto -c -k --sequesterRsrc --keepParent "$PACKAGE_DIR" "$ZIP_PATH"

echo "$PACKAGE_DIR"
echo "$ZIP_PATH"
