#!/usr/bin/env python3
"""
Query the RAG knowledge base and optionally pass context to Claude
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def query_rag(question: str, top_k: int = 3):
    """Query the RAG system and return context"""
    response = requests.post(
        f"{BASE_URL}/query",
        json={"question": question, "top_k": top_k}
    )

    if response.status_code == 404:
        print("No documents found. Embed some docs first with: python embed_docs.py")
        return None

    result = response.json()
    return result

def print_context(result: dict):
    """Pretty print the retrieved context"""
    print(f"\nQuestion: {result['question']}")
    print("\n" + "="*60 + "\n")

    for i, (context, source) in enumerate(zip(result['context'], result['sources']), 1):
        print(f"[Source: {source}]")
        print(context[:500] + "..." if len(context) > 500 else context)
        print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_rag.py \"your question\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = query_rag(question)

    if result:
        print_context(result)
