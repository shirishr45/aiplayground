#!/bin/bash

# Script to configure Claude Code to use a local model server
# Works with Ollama, llama.cpp, or any Anthropic-compatible API server
# Usage:
#   ./launch_claude_local.sh         # Launch claude with local model
#   source ./launch_claude_local.sh  # Configure shell only, no launch
#   ./launch_claude_local.sh --no-claude  # Output commands for eval

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
MODEL_NAME="qwen3.5:27b"
BASE_URL="http://sriserver:8081"
API_KEY="dummy"

SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Detect if script is being executed directly (not sourced)
# When executed: BASH_SOURCE[0] == $0
# When sourced: BASH_SOURCE[0] != $0 (or BASH_SOURCE[1] points to the shell)
SOURCED=false
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    SOURCED=true
fi

LAUNCH_CLAUDE=true

# Function to print usage
usage() {
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -m, --model      Specify model name (default: $MODEL_NAME)"
    echo "  -u, --url        Specify base URL (default: $BASE_URL)"
    echo "  -k, --key        Specify API key (default: $API_KEY)"
    echo "  -n, --no-claude  Configure only, do not launch claude"
    echo ""
    echo "Example: $SCRIPT_NAME"
    echo "Example: $SCRIPT_NAME --model my-custom-model"
    echo "Example: $SCRIPT_NAME --no-claude"
}

# Parse command line arguments
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

# Determine whether to execute exports or echo them
# Execute when: sourced OR running directly to launch claude
# Echo when: run directly with --no-claude (user will eval the output)
DO_EXPORT=true
if ! $SOURCED && ! $LAUNCH_CLAUDE; then
    DO_EXPORT=false
fi

# Activate virtual environment if it exists
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

# Configure Claude Code to use the local model server
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

# Final message
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

# Launch claude by default (only works when running directly, not sourced)
if $LAUNCH_CLAUDE; then
    if $SOURCED; then
        echo "Note: Use './launch_claude_local.sh' (not source) to launch claude."
    else
        echo "Launching claude..."
        exec claude
    fi
fi
