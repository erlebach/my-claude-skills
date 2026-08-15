#!/usr/bin/env bash
# Portable entry point: run the YAML→HTML compiler from this skill folder.
# Usage: ./compile.sh INPUT.yaml OUTPUT.html [--embed-images]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$ROOT"
exec python3 -m compiler "$@"
