#!/bin/bash

# Qwen3.5-27B Q4_K_M — CLI chat or Web UI server
# Optimized for: Apple M1 Max, 8 perf cores, 64GB RAM
#
# Usage:
#   ./qwen.sh            # interactive CLI chat
#   ./qwen.sh --serve    # web UI at http://localhost:8080

MODEL_REPO="bartowski/Qwen_Qwen3.5-27B-GGUF:Q4_K_M"

COMMON_FLAGS=(
  --hf-repo "$MODEL_REPO"
  --ctx-size 8192
  --n-gpu-layers 999
  --threads 8
  --threads-batch 8
  --batch-size 512
  --ubatch-size 256
  --flash-attn on
  --mlock
  --cache-type-k q8_0
  --cache-type-v q8_0
  --jinja
  --chat-template-kwargs '{"enable_thinking": false}'
  --reasoning-budget 0
)

if [[ "$1" == "--serve" ]]; then
  shift
  HOST="${HOST:-127.0.0.1}"
  PORT="${PORT:-8080}"
  echo "Starting server at http://${HOST}:${PORT}"
  exec llama-server \
    "${COMMON_FLAGS[@]}" \
    --host "$HOST" \
    --port "$PORT" \
    "$@"
else
  exec llama-cli \
    "${COMMON_FLAGS[@]}" \
    --conversation \
    "$@"
fi
