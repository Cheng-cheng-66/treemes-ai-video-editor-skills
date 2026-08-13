#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL: Python 3.11+ is required."
  exit 1
fi

missing=""
command -v ffmpeg >/dev/null 2>&1 || missing="$missing ffmpeg"
command -v ffprobe >/dev/null 2>&1 || missing="$missing ffprobe"
command -v node >/dev/null 2>&1 || missing="$missing node"
if [ -n "$missing" ]; then
  echo "FAIL: missing system commands:$missing"
  echo "Install FFmpeg and Node.js, then rerun this script."
  exit 2
fi

exec python3 "$PROJECT_DIR/scripts/bootstrap.py"
