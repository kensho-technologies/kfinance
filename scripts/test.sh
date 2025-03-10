#!/usr/bin/env bash
# Copyright 2025-present Kensho Technologies, LLC.
set -euxo pipefail

python -m pytest -s --cov=kfinance "$@"
