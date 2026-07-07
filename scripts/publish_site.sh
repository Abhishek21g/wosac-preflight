#!/usr/bin/env bash
# Publish dashboard to enaguthi.com/wosac-preflight/site/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_REPO="${HOME}/Documents/Abhishek21g.github.io"
DEST="${SITE_REPO}/wosac-preflight/site"
PUBLIC_DEST="${SITE_REPO}/public/wosac-preflight/site"

for target in "$DEST" "$PUBLIC_DEST"; do
  mkdir -p "$target"
  cp "$ROOT/dashboard/index.html" "$target/"
  cp "$ROOT/dashboard/styles.css" "$target/"
  cp "$ROOT/dashboard/app.js" "$target/"
  cp "$ROOT/dashboard/favicon.svg" "$target/"
  cp "$ROOT/dashboard/sample_receipt.json" "$target/"
  echo "→ $target"
done

echo ""
echo "Published locally. Commit Abhishek21g.github.io and push to go live:"
echo "  cd $SITE_REPO && git add wosac-preflight public/wosac-preflight && git commit -m 'Publish WOSAC Preflight site' && git push"
