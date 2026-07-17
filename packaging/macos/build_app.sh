#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION="$(<"$REPO_ROOT/VERSION")"
OUTPUT=""
LINKED_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --linked-root)
      LINKED_ROOT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$OUTPUT" ]]; then
  echo "Usage: $0 --output /path/to/Hedgehog\\ Master.app [--linked-root /path/to/repo]" >&2
  exit 2
fi

APP_DIR="$OUTPUT"
CONTENTS_DIR="$APP_DIR/Contents"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
MACOS_DIR="$CONTENTS_DIR/MacOS"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

rm -rf "$APP_DIR"
mkdir -p "$RESOURCES_DIR" "$MACOS_DIR"
cp "$SCRIPT_DIR/launcher.sh" "$MACOS_DIR/hedgehog-master"
chmod +x "$MACOS_DIR/hedgehog-master"
sed "s/__VERSION__/$VERSION/g" "$SCRIPT_DIR/Info.plist.in" > "$CONTENTS_DIR/Info.plist"
printf '%s\n' "$VERSION" > "$RESOURCES_DIR/version"

if [[ -n "$LINKED_ROOT" ]]; then
  PYTHON_PATH=""
  if [[ -x "$LINKED_ROOT/.venv/bin/python" ]]; then
    PYTHON_PATH="$("$LINKED_ROOT/.venv/bin/python" -c 'import sys; print(sys._base_executable)')"
  fi
  RUNTIME_ROOT="$("$SCRIPT_DIR/install_runtime.sh" --source-root "$LINKED_ROOT" --python "$PYTHON_PATH")"
  printf '%s\n' "$RUNTIME_ROOT" > "$RESOURCES_DIR/runtime-root"
  printf '%s\n' "$(cd "$RUNTIME_ROOT/.." && pwd)/.venv/bin/python" > "$RESOURCES_DIR/python-path"
fi

ICON_SOURCE="$REPO_ROOT/assets/branding/hm-mark.svg"
ICONSET="$TMP_DIR/AppIcon.iconset"
mkdir -p "$ICONSET" "$TMP_DIR/render"
qlmanage -t -s 1024 -o "$TMP_DIR/render" "$ICON_SOURCE" >/dev/null 2>&1
RENDERED_ICON="$TMP_DIR/render/$(basename "$ICON_SOURCE").png"

for specification in \
  "16 icon_16x16.png" \
  "32 icon_16x16@2x.png" \
  "32 icon_32x32.png" \
  "64 icon_32x32@2x.png" \
  "128 icon_128x128.png" \
  "256 icon_128x128@2x.png" \
  "256 icon_256x256.png" \
  "512 icon_256x256@2x.png" \
  "512 icon_512x512.png" \
  "1024 icon_512x512@2x.png"; do
  size="${specification%% *}"
  filename="${specification#* }"
  sips -z "$size" "$size" "$RENDERED_ICON" --out "$ICONSET/$filename" >/dev/null
done

iconutil -c icns "$ICONSET" -o "$RESOURCES_DIR/AppIcon.icns"
codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1
echo "$APP_DIR"
