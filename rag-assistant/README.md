# RAG Chat Assistant for Structural Engineering

Persistent knowledge base with local LLM (Ollama/llama.cpp).

## Quick Start

```bash
# 1. Activate your venv
cd /Users/shirish/aiplayground
source .venv/bin/activate

# 2. Drop PDFs into the knowledge_base folder
#    (e.g., cp steel_codes.pdf rag-assistant/knowledge_base/)

# 3. Run the assistant
cd rag-assistant
python run.py
```

That's it. It will:
- Install dependencies automatically
- Embed your PDFs
- Start an interactive chat

## Requirements

- **Ollama** (recommended): Install from https://ollama.ai
  - Run `ollama serve` in a separate terminal
  - Pull a model: `ollama pull llama3.3`

- **Or llama.cpp**: Already have it. RAG will work in summary mode without Ollama.

## Files

- `run.py` - **Main script** (embed + chat)
- `knowledge_base/` - Put your PDFs here
- `chroma_db/` - Persistent vector DB (auto-created)

## Advanced (API Server)

For querying via API or integrating with Claude:

```bash
# Install extra deps
pip install fastapi uvicorn

# Start server
python rag_server.py

# Query from another terminal
python query_rag.py "your question"
```
