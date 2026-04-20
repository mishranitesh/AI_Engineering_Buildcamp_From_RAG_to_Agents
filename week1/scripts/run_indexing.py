"""
Entry-point script for building search index.

This script:
1. Prepares documents
2. Chunks them
3. Converts chunks to indexable format
4. Builds index
5. Prints number of indexed documents
"""

from src.processing.chunking import chunk_all_documents
from src.indexing.build_index import build_index


if __name__ == "__main__":
    # Step 1: Create chunks
    chunks = chunk_all_documents(
        input_dir="data/processed/",
        size=100,
        step=50
    )

    print(f"Total chunks: {len(chunks)}")

    # Step 2: Build index
    index, documents = build_index(chunks)

    # Step 3: Print number of indexed documents
    print(f"Indexed documents: {len(documents)}")