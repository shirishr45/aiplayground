#!/bin/bash

# Local LLM Model Switcher — browser UI for picking and hot-swapping models
# Management UI: http://localhost:8079
# llama-server:  http://localhost:8080  (started from the browser UI)

exec python3 "$(dirname "$0")/model_switcher.py" "$@"
