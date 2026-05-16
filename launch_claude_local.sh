#!/bin/bash

# Script to configure Claude Code to use a local model server
# Works with Ollama, llama.cpp, or any Anthropic-compatible API server
# Usage:
#   ./launch_claude_local.sh         # Select model interactively, then launch claude
#   ./launch_claude_local.sh -m <id> # Skip menu, use specified model ID
#   source ./launch_claude_local.sh  # Configure shell only, no launch
#   ./launch_claude_local.sh --no-claude  # Output commands for eval

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ── Model definitions (parallel arrays, must match serve.sh order) ────────────
MODEL_NAMES=(
  "Qwen3.5-27B  Q4_K_M  (~16GB)"
  "Qwen3.5-27B  Q8_0    (~28GB, higher quality)"
  "Qwen3-32B    Q4_K_M  (~20GB)"
  "Qwen3.5-35B-A3B Q4_K_M (~20GB, MoE)"
  "Qwen3.6-35B-A3B Q4_K_M (~20GB, MoE)"
  "Qwen3-30B-A3B Q4_K_M (~18GB, MoE — fastest)"
  "Llama-3.3-70B Q4_K_M (~40GB)"
  "Hermes-3-Llama-3.1-70B Q4_K_M (~40GB, tool calling)"
)

# Model identifiers passed to Claude Code via ANTHROPIC_MODEL
MODEL_IDS=(
  "qwen3.5-27b-q4"
  "qwen3.5-27b-q8"
  "qwen3-32b-q4"
  "qwen3.5-35b-a3b-q4"
  "qwen3.6-35b-a3b-q4"
  "qwen3-30b-a3b-q4"
  "llama-3.3-70b-q4"
  "hermes-3-llama-3.1-70b-q4"
)

# ── Defaults ──────────────────────────────────────────────────────────────────
MODEL_NAME=""
BASE_URL="http://127.0.0.1:8080"
API_KEY="dummy"
LAUNCH_CLAUDE=true

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Detect if script is being sourced
SOURCED=false
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    SOURCED=true
fi

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -m, --model      Override model ID (skips interactive menu)"
    echo "  -u, --url        Specify base URL (default: $BASE_URL)"
    echo "  -k, --key        Specify API key (default: $API_KEY)"
    echo "  -n, --no-claude  Configure only, do not launch claude"
    echo ""
    echo "Example: $SCRIPT_NAME"
    echo "Example: $SCRIPT_NAME --model qwen3.5-27b-q4"
    echo "Example: $SCRIPT_NAME --no-claude"
}

# ── Parse command line arguments ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -m|--model)
            MODEL_NAME="$2"
            shift 2
            ;;
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -k|--key)
            API_KEY="$2"
            shift 2
            ;;
        -n|--no-claude)
            LAUNCH_CLAUDE=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# ── Model selection menu (skipped if -m was provided) ─────────────────────────
if [[ -z "$MODEL_NAME" ]]; then
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│      Claude Local — Select a Model          │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    for i in "${!MODEL_NAMES[@]}"; do
        echo "  $((i+1))) ${MODEL_NAMES[$i]}"
    done
    echo "  $((${#MODEL_NAMES[@]}+1))) Quit"
    echo ""

    while true; do
        read -r -p "Enter number: " _choice
        if [[ "$_choice" =~ ^[0-9]+$ ]]; then
            if [[ "$_choice" -eq $(( ${#MODEL_NAMES[@]}+1 )) ]]; then
                echo "Bye."
                exit 0
            elif [[ "$_choice" -ge 1 && "$_choice" -le "${#MODEL_NAMES[@]}" ]]; then
                _idx=$((_choice-1))
                break
            fi
        fi
        echo "Invalid selection, try again."
    done

    MODEL_NAME="${MODEL_IDS[$_idx]}"
    echo ""
    echo "Selected : ${MODEL_NAMES[$_idx]}"
    echo "Model ID : $MODEL_NAME"
    echo ""
fi

# ── Determine whether to execute exports or echo them ─────────────────────────
# Execute when: sourced OR running directly to launch claude
# Echo when: run directly with --no-claude (user will eval the output)
DO_EXPORT=true
if ! $SOURCED && ! $LAUNCH_CLAUDE; then
    DO_EXPORT=false
fi

# ── Activate virtual environment if it exists ─────────────────────────────────
if [ -f "venv/bin/activate" ]; then
    if $DO_EXPORT; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "# Activating virtual environment..."
        echo "source venv/bin/activate"
    fi
elif [ -f "venv/Scripts/activate" ]; then
    if $DO_EXPORT; then
        echo "Activating virtual environment..."
        source venv/Scripts/activate
    else
        echo "# Activating virtual environment..."
        echo "source venv/Scripts/activate"
    fi
else
    echo "No virtual environment found in current directory"
fi

# ── Configure Claude Code ──────────────────────────────────────────────────────
if $DO_EXPORT; then
    echo "Configuring Claude Code for local model: $MODEL_NAME"
    echo "Base URL: $BASE_URL"
else
    echo "# Configuring Claude Code for local model: $MODEL_NAME"
    echo "# Base URL: $BASE_URL"
fi

# 1. Point Claude Code at your local model server
if $DO_EXPORT; then
    export ANTHROPIC_BASE_URL="$BASE_URL"
else
    echo "export ANTHROPIC_BASE_URL=\"$BASE_URL\""
fi

# 2. Auth (your local server's API key, or a dummy value if not needed)
if $DO_EXPORT; then
    export ANTHROPIC_API_KEY="$API_KEY"
else
    echo "export ANTHROPIC_API_KEY=\"$API_KEY\""
fi

# 3. Main conversation model
if $DO_EXPORT; then
    export ANTHROPIC_MODEL="$MODEL_NAME"
else
    echo "export ANTHROPIC_MODEL=\"$MODEL_NAME\""
fi

# 4. Small/fast model (used for token counting, API key verification, etc.)
if $DO_EXPORT; then
    export ANTHROPIC_SMALL_FAST_MODEL="$MODEL_NAME"
else
    echo "export ANTHROPIC_SMALL_FAST_MODEL=\"$MODEL_NAME\""
fi

# 5. Subagent model (used by the Agent tool for spawned subagents)
if $DO_EXPORT; then
    export CLAUDE_CODE_SUBAGENT_MODEL="$MODEL_NAME"
else
    echo "export CLAUDE_CODE_SUBAGENT_MODEL=\"$MODEL_NAME\""
fi

# 6. Override the default aliases so "sonnet", "opus", "haiku" all resolve to your model
if $DO_EXPORT; then
    export ANTHROPIC_DEFAULT_SONNET_MODEL="$MODEL_NAME"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="$MODEL_NAME"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="$MODEL_NAME"
else
    echo "export ANTHROPIC_DEFAULT_SONNET_MODEL=\"$MODEL_NAME\""
    echo "export ANTHROPIC_DEFAULT_OPUS_MODEL=\"$MODEL_NAME\""
    echo "export ANTHROPIC_DEFAULT_HAIKU_MODEL=\"$MODEL_NAME\""
fi

# 7. Disable nonessential traffic
if $DO_EXPORT; then
    export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
else
    echo "export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
fi

# ── Final message ──────────────────────────────────────────────────────────────
if $DO_EXPORT; then
    echo ""
    echo "Claude Code is now configured to use: $MODEL_NAME"
    if $SOURCED && ! $LAUNCH_CLAUDE; then
        echo ""
        echo "Note: These settings are only for the current shell session."
        echo "Tip: Use 'eval \"\$(./launch_claude_local.sh --no-claude)\"' for the same effect."
        echo ""
        echo "To make these settings permanent, add to ~/.bashrc:"
        echo ""
        echo "  export ANTHROPIC_BASE_URL=\"$BASE_URL\""
        echo "  export ANTHROPIC_API_KEY=\"$API_KEY\""
        echo "  export ANTHROPIC_MODEL=\"$MODEL_NAME\""
        echo "  export ANTHROPIC_SMALL_FAST_MODEL=\"$MODEL_NAME\""
        echo "  export CLAUDE_CODE_SUBAGENT_MODEL=\"$MODEL_NAME\""
        echo ""
        echo "Then run: source ~/.bashrc"
    fi
elif ! $SOURCED && ! $LAUNCH_CLAUDE; then
    echo ""
    echo "# Claude Code is now configured to use: $MODEL_NAME"
    echo "# Run 'eval \"\$(./launch_claude_local.sh --no-claude)\"' to apply these settings"
fi

# ── Launch claude ──────────────────────────────────────────────────────────────
if $LAUNCH_CLAUDE; then
    if $SOURCED; then
        echo "Note: Use './launch_claude_local.sh' (not source) to launch claude."
    else
        echo "Launching claude..."
        exec claude
    fi
fi
