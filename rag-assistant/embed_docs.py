#!/usr/bin/env python3
"""
Embed documents from knowledge_base folder into ChromaDB
Run this after adding new PDFs/text files
"""

import os
import sys
from pathlib import Path

try:
    from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbeddings
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Installing LlamaIndex dependencies...")
    os.system(f'"{sys.executable}" -m pip install llama-index llama-index-readers-pdf llama-index-vector-stores-chroma llama-index-embeddings-huggingface pypdf')
    from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbeddings
    import chromadb
    from chromadb.config import Settings

BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "knowledge_base"
DB_DIR = BASE_DIR / "chroma_db"

def embed_documents():
    # Initialize ChromaDB
    client = chromadb.Client(Settings(
        chroma_db_path=str(DB_DIR),
        anonymized_telemetry=False
    ))

    # Create vector store
    chroma_collection = client.get_or_create_collection(name="structural_engineering")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Use local embeddings (works offline)
    embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    # Find all documents
    pdf_files = list(KB_DIR.glob("*.pdf"))
    txt_files = list(KB_DIR.glob("*.txt"))
    md_files = list(KB_DIR.glob("*.md"))
    all_files = pdf_files + txt_files + md_files

    if not all_files:
        print("No documents found in knowledge_base folder.")
        print(f"Drop PDFs, TXT, or MD files into: {KB_DIR}")
        return

    print(f"Found {len(all_files)} documents to embed...")

    # Load documents
    documents = []
    for file_path in all_files:
        try:
            if file_path.suffix == ".pdf":
                from llama_index.readers.file import PDFReader
                reader = PDFReader()
                docs = reader.load_data(file_path)
            else:
                reader = SimpleDirectoryReader(input_files=[file_path])
                docs = reader.load_data()
            documents.extend(docs)
            print(f"  Loaded: {file_path.name}")
        except Exception as e:
            print(f"  Error loading {file_path.name}: {e}")

    if not documents:
        print("No documents could be loaded.")
        return

    # Create index and store
    print(f"Creating embeddings for {len(documents)} document chunks...")
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
    )

    print(f"Done! Embedded {len(documents)} chunks from {len(all_files)} files.")

if __name__ == "__main__":
    embed_documents()
