#!/bin/bash

# Local LLM Server — choose a model then launch web UI at http://localhost:8080
# Optimized for: Apple M1 Max, 8 perf cores, 64GB RAM

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"

# ── Model definitions (parallel arrays) ───────────────────────────────────────
NAMES=(
  "Qwen3.5-27B  Q4_K_M  (~16GB)"
  "Qwen3.5-27B  Q8_0    (~28GB, higher quality)"
  "Qwen3-32B    Q4_K_M  (~20GB)"
  "Qwen3.5-35B-A3B Q4_K_M (~20GB, MoE)"
  "Qwen3.6-35B-A3B Q4_K_M (~20GB, MoE)"
  "Qwen3-30B-A3B Q4_K_M (~18GB, MoE — fastest)"
  "Qwen3.6-35B-A3B-MTP UD-Q4_K_M (~23GB, MoE, Unsloth)"
  "Llama-3.3-70B Q4_K_M (~40GB)"
  "Hermes-3-Llama-3.1-70B Q4_K_M (~40GB, tool calling)"
)

REPOS=(
  "bartowski/Qwen_Qwen3.5-27B-GGUF:Q4_K_M"
  "/Users/shirish/.lmstudio/models/lmstudio-community/Qwen3.5-27B-GGUF/Qwen3.5-27B-Q8_0.gguf"
  "bartowski/Qwen_Qwen3-32B-GGUF:Q4_K_M"
  "/Users/shirish/.lmstudio/models/lmstudio-community/Qwen3.5-35B-A3B-GGUF/Qwen3.5-35B-A3B-Q4_K_M.gguf"
  "models/Qwen_Qwen3.6-35B-A3B-Q4_K_M.gguf"
  "bartowski/Qwen_Qwen3-30B-A3B-GGUF:Q4_K_M"
  "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_M"
  "bartowski/Llama-3.3-70B-Instruct-GGUF:Q4_K_M"
  "NousResearch/Hermes-3-Llama-3.1-70B-GGUF:Q4_K_M"
)

CTX=(
  32768   # Qwen3.5-27B  Q4 — 36GB available after weights
  32768   # Qwen3.5-27B  Q8 — 24GB available after weights
  32768   # Qwen3-32B    — 32GB available after weights
  32768   # Qwen3.5-35B-A3B — 32GB available after weights
  32768   # Qwen3.6-35B-A3B — 32GB available after weights
  32768   # Qwen3-30B-A3B — 34GB available after weights
  32768   # Qwen3.6-35B-A3B-MTP — 32GB available after weights
  65536   # Llama-3.3-70B — 12GB available, can push to 64K
  32768   # Hermes-3-70B  — 12GB available after weights
)

EXTRA=(
  "--reasoning off"
  "--reasoning off"
  "--reasoning off"
  "--reasoning off"
  "--reasoning off"
  "--reasoning off"
  "--reasoning off --spec-type draft-mtp"
  ""
  ""
)

# ── Menu ───────────────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│         Local LLM — Select a Model          │"
echo "└─────────────────────────────────────────────┘"
echo ""

for i in "${!NAMES[@]}"; do
  echo "  $((i+1))) ${NAMES[$i]}"
done
echo "  $((${#NAMES[@]}+1))) Quit"
echo ""

while true; do
  read -r -p "Enter number: " choice
  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    if [[ "$choice" -eq $(( ${#NAMES[@]}+1 )) ]]; then
      echo "Bye."
      exit 0
    elif [[ "$choice" -ge 1 && "$choice" -le "${#NAMES[@]}" ]]; then
      idx=$((choice-1))
      break
    fi
  fi
  echo "Invalid selection, try again."
done

REPO="${REPOS[$idx]}"
NAME="${NAMES[$idx]}"
CTX_SIZE="${CTX[$idx]}"
EXTRA_FLAGS="${EXTRA[$idx]}"

# ── Launch ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Determine model source flag: absolute path, relative local file, or HF repo
if [[ "$REPO" == /* ]]; then
  MODEL_FLAG="--model ${REPO}"
  echo ""
  echo "Model : $NAME"
  echo "File  : $REPO"
elif [[ "$REPO" == *.gguf ]]; then
  MODEL_FLAG="--model ${SCRIPT_DIR}/${REPO}"
  echo ""
  echo "Model : $NAME"
  echo "File  : ${SCRIPT_DIR}/${REPO}"
else
  MODEL_FLAG="--hf-repo ${REPO}"
  echo ""
  echo "Model : $NAME"
  echo "Repo  : $REPO"
fi
echo "URL   : http://${HOST}:${PORT}"
echo ""

eval llama-server \
  $MODEL_FLAG \
  --host "$HOST" \
  --port "$PORT" \
  --ctx-size "$CTX_SIZE" \
  --n-gpu-layers 999 \
  --threads 8 \
  --threads-batch 8 \
  --batch-size 512 \
  --ubatch-size 256 \
  --flash-attn on \
  --mlock \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --jinja \
  $EXTRA_FLAGS
