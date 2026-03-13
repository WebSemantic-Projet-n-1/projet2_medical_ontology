#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: $0 <chrome|firefox>"
    exit 1
}

[ $# -eq 1 ] || usage
TARGET="$1"
[[ "$TARGET" == "chrome" || "$TARGET" == "firefox" ]] || usage

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIVE="$DIR/manifest.json"
SOURCE="$DIR/manifest-$TARGET.json"

if [ ! -f "$SOURCE" ]; then
    echo "Error: $SOURCE not found." >&2
    exit 1
fi

cp "$SOURCE" "$ACTIVE"
echo "Switched to $TARGET. Load the 'extensions' folder in your browser."
