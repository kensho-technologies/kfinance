#!/usr/bin/env bash
# Copyright 2025-present Kensho Technologies, LLC.
set -euxo pipefail

fix="";
while getopts ":f" opt; do
  case $opt in
    f) fix="--fix" ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

python -m mypy --config-file pyproject.toml kfinance

if [ "$fix" = "--fix" ]; then
  python -m ruff --config pyproject.toml check kfinance --fix
else
  python -m ruff --config pyproject.toml check kfinance
fi
