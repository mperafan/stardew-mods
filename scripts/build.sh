#!/usr/bin/env bash
# Packages the mod into a Nexus-style zip: dist/SebastianCabezaDeCoco-<version>.zip
# Usage: ./scripts/build.sh
set -euo pipefail                       # stop on any error, unset var, or failed pipe
cd "$(dirname "$0")/.."                 # run from the repo root no matter where it's called from

MOD=SebastianCabezaDeCoco
VERSION=$(python3 -c "import json; print(json.load(open('$MOD/manifest.json'))['Version'])")

# Validate JSON so a typo never ships (SMAPI would silently skip a broken mod)
for f in "$MOD"/*.json; do python3 -m json.tool "$f" > /dev/null || { echo "Invalid JSON: $f"; exit 1; }; done

mkdir -p dist
rm -f "dist/$MOD-$VERSION.zip"
zip -r -X "dist/$MOD-$VERSION.zip" "$MOD" -x '*.DS_Store'
echo "Built dist/$MOD-$VERSION.zip"
