"""
Entry-point script for preparing and chunking markdown books.

What this script does:
1. Reads markdown files from data/processed/
2. Splits them into lines
3. Removes empty lines
4. Chunks them using gitsource
5. Prints chunk statistics for inspection
"""

from collections import defaultdict
from src.processing.chunking import prepare_documents, chunk_all_documents


if __name__ == "__main__":
    # Prepare cleaned documents from markdown files
    documents = prepare_documents("data/processed/")

    # Let's check length of each prepared document
    for document in documents:
        print(f"documents: {document["source"]}, length: {len(document["content"])}")

    # Print how many books were prepared
    print(f"Prepared {len(documents)} documents")

    # Chunk all documents using homework settings
    chunks = chunk_all_documents(
        input_dir="data/processed/",
        size=100,
        step=50
    )

    # Print total number of chunks across all books
    print(f"Total chunks created: {len(chunks)}")

     # Step 3: Group chunks by source (book filename)
    chunks_by_source = defaultdict(int)

    for chunk in chunks:
        source = chunk["source"]
        chunks_by_source[source] += 1

    # Step 4: Print chunk counts per book
    print("\n📊 Chunk count per book:\n")

    for source, count in chunks_by_source.items():
        print(f"{source}: {count}")