#!/bin/bash

set -euo pipefail

sudo curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv --allow-existing

source .venv/bin/activate

uv sync

pre-commit install
