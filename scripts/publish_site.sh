#!/usr/bin/env bash
# Publish dashboard to enaguthi.com/wosac-preflight/site/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_ROOT="${HOME}/Projects/Abhishek21g.github.io/wosac-preflight/site"
mkdir -p "$SITE_ROOT"
cp "$ROOT/dashboard/index.html" "$SITE_ROOT/"
cp "$ROOT/dashboard/sample_receipt.json" "$SITE_ROOT/"
echo "Copied to $SITE_ROOT"
echo "Commit and push Abhishek21g.github.io to publish."
