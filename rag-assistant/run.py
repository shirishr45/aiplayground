#!/usr/bin/env python3
"""
RAG Chat Assistant - Single Script
Usage: python run.py
- Embeds PDFs from knowledge_base/ folder
- Starts a local RAG chat interface
- Uses llama.cpp for local LLM inference
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "knowledge_base"
DB_DIR = BASE_DIR / "chroma_db"

# Ensure directories exist
KB_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

def check_dependencies():
    """Install missing dependencies"""
    required = [
        "chromadb",
        "llama-index",
        "llama-index-readers-pdf",
        "llama-index-vector-stores-chroma",
        "llama-index-embeddings-huggingface",
        "llama-index-llms-ollama",
        "pypdf",
        "rich"
    ]

    print("Checking dependencies...")
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"  Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
    print("  Done!")

def embed_documents():
    """Embed all PDFs in knowledge_base folder"""
    from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.readers.file import PDFReader
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbeddings
    import chromadb
    from chromadb.config import Settings

    # Find documents
    pdf_files = list(KB_DIR.glob("*.pdf"))
    txt_files = list(KB_DIR.glob("*.txt"))
    md_files = list(KB_DIR.glob("*.md"))
    all_files = pdf_files + txt_files + md_files

    if not all_files:
        print(f"\nNo documents found in: {KB_DIR}")
        print("Add PDFs, TXT, or MD files there first.")
        return None

    print(f"\nFound {len(all_files)} document(s):")
    for f in all_files:
        print(f"  - {f.name}")

    # Initialize ChromaDB
    client = chromadb.Client(Settings(
        chroma_db_path=str(DB_DIR),
        anonymized_telemetry=False
    ))
    chroma_collection = client.get_or_create_collection(name="structural_engineering")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Use local embeddings
    print("\nLoading embedding model (one-time download)...")
    embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    # Load documents
    documents = []
    for file_path in all_files:
        try:
            if file_path.suffix == ".pdf":
                reader = PDFReader()
                docs = reader.load_data(file_path)
            else:
                reader = SimpleDirectoryReader(input_files=[file_path])
                docs = reader.load_data()
            documents.extend(docs)
            print(f"  Loaded {len(docs)} chunks from {file_path.name}")
        except Exception as e:
            print(f"  Error loading {file_path.name}: {e}")

    if not documents:
        print("\nNo documents could be loaded.")
        return None

    # Create index
    print(f"\nEmbedding {len(documents)} chunks...")
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
    )
    print("Done!")
    return index

def chat_with_rag(index):
    """Interactive chat using RAG + local LLM via Ollama"""
    from llama_index.core import QueryEngine
    from llama_index.llms.ollama import Ollama
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Check if Ollama is running
    try:
        import requests
        requests.get("http://localhost:11434", timeout=2)
    except:
        console.print("[yellow]Ollama doesn't seem to be running.[/yellow]")
        console.print("Start it with: [bold]ollama serve[/bold]")
        console.print()
        console.print("Or use your existing llama.cpp setup instead.")
        console.print("For now, I'll use a simple summary mode.")
        use_ollama = False
    else:
        use_ollama = True

    # Create query engine
    if use_ollama:
        console.print("[green]Using Ollama for local LLM...[/green]")
        llm = Ollama(model="llama3.3", request_timeout=120.0)
        query_engine = index.as_query_engine(llm=llm)
    else:
        query_engine = index.as_query_engine()

    console.print()
    console.print(Panel.fit(
        "[bold]RAG Chat Assistant[/bold]\n"
        "Ask questions about your structural engineering documents.\n"
        "Type [bold]'quit'[/bold] to exit."
    ))

    while True:
        try:
            question = console.input("\n[blue]You[/blue] > ").strip()
        except KeyboardInterrupt:
            console.print("\n[bold]Goodbye![/bold]")
            break

        if question.lower() in ["quit", "exit", "q"]:
            console.print("[bold]Goodbye![/bold]")
            break

        if not question:
            continue

        console.print("[yellow]Thinking...[/yellow]")

        try:
            if use_ollama:
                response = query_engine.query(question)
                answer = str(response)
            else:
                # Fallback: just show retrieved context
                response = query_engine.query(question)
                answer = "Here's what I found in your documents:\n\n"
                for i, node in enumerate(response.source_nodes, 1):
                    score = round(node.score * 100, 1)
                    answer += f"[{i}] (relevance: {score}%)\n{node.text[:300]}...\n\n"

            console.print(f"\n[green]Assistant[/green] > {answer}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

def main():
    print("="*60)
    print("  RAG Chat Assistant - Structural Engineering")
    print("="*60)

    # Check dependencies
    check_dependencies()

    # Embed documents
    index = embed_documents()
    if index is None:
        sys.exit(1)

    # Start chat
    chat_with_rag(index)

if __name__ == "__main__":
    main()
