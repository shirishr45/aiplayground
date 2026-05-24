#!/bin/bash

# Local LLM Server — router mode with in-UI model dropdown
# Open http://localhost:8080 and use the model selector in the top bar.
# Optimized for: Apple M1 Max, 8 perf cores, 64GB RAM

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  llama-server (router mode) → http://${HOST}:${PORT}"
echo "  Select a model from the dropdown in the web UI."
echo ""

llama-server \
  --models-preset "${SCRIPT_DIR}/models.ini" \
  --models-max 1 \
  --no-models-autoload \
  --host "$HOST" \
  --port "$PORT"
