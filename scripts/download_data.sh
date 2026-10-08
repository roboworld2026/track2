#!/usr/bin/env bash
set -euo pipefail
exec "${HAVLN_PYTHON:-python3}" "$(dirname "${BASH_SOURCE[0]}")/download_resources.py" "$@"
