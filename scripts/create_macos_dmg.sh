#!/usr/bin/env bash
set -euo pipefail

VERSION="$(tr -d '[:space:]' < VERSION)"
APP="dist/DigitalCrown.app"
STAGE="build/macos/dmg-root"
OUT="dist_macos/DigitalCrown-${VERSION}-arm64.dmg"

[[ -d "$APP" ]] || { echo "Missing $APP" >&2; exit 1; }
rm -rf "$STAGE" dist_macos
mkdir -p "$STAGE" dist_macos

# ditto preserves the signed bundle structure, symlinks and metadata.
ditto "$APP" "$STAGE/DigitalCrown.app"
ln -s /Applications "$STAGE/Applications"

hdiutil create \
  -volname "Digital Crown" \
  -srcfolder "$STAGE" \
  -ov \
  -format UDZO \
  "$OUT"

echo "P7_DMG_BUILD=SUCCESS path=$OUT"
