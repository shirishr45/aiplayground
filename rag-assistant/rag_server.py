#!/usr/bin/env python3
"""
Local RAG Server for Structural Engineering Knowledge Base
- Embeds PDFs/text files into a local vector database
- Serves a simple API for querying the knowledge base
- Works with your existing local LLM setup (llama.cpp)
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict

# Check dependencies
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Installing dependencies...")
    os.system(f'"{sys.executable}" -m pip install chromadb llama-index llama-index-readers-pdf pypdf')
    import chromadb
    from chromadb.config import Settings

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Paths
BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "knowledge_base"
DB_DIR = BASE_DIR / "chroma_db"

# Initialize directories
KB_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Initialize ChromaDB (persistent, local)
client = chromadb.Client(Settings(
    chroma_db_path=str(DB_DIR),
    anonymized_telemetry=False
))

# Create collection
collection = client.get_or_create_collection(name="structural_engineering")

app = FastAPI(title="Structural Engineering RAG Server")


class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    question: str
    context: List[str]
    sources: List[str]


@app.get("/")
def health():
    return {"status": "ok", "docs_count": collection.count()}


@app.post("/embed_docs")
def embed_docs():
    """Scan KB_DIR and embed all PDFs/text files"""
    import subprocess

    # Run embedding script
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "embed_docs.py")],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {"error": result.stderr}

    return {
        "status": "success",
        "message": result.stdout,
        "total_docs": collection.count()
    }


@app.post("/query", response_model=QueryResponse)
def query_knowledge_base(request: QueryRequest):
    """Search the knowledge base and return relevant context"""
    results = collection.query(
        query_texts=[request.question],
        n_results=request.top_k
    )

    if not results["documents"][0]:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Try embedding docs first with POST /embed_docs"
        )

    return QueryResponse(
        question=request.question,
        context=results["documents"][0],
        sources=results["metadatas"][0].get("source", []) if results["metadatas"][0] else []
    )


@app.get("/docs")
def list_docs():
    """List all embedded documents"""
    all_docs = collection.get()
    return {
        "count": all_docs["ids"],
        "sources": list(set(m.get("source", "unknown") for m in all_docs["metadatas"] or []))
    }


if __name__ == "__main__":
    print("Starting RAG server on http://localhost:8000")
    print(f"Knowledge base directory: {KB_DIR}")
    print("Drop your PDFs/text files into the knowledge_base folder, then call POST /embed_docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
