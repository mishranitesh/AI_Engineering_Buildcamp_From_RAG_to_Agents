"""
Search the minsearch index and inspect the top result.
"""

from src.processing.chunking import chunk_all_documents
from src.indexing.build_index import build_index

if __name__ == "__main__":
    # Create chunks from processed markdown files
    chunks = chunk_all_documents(
        input_dir="data/processed/",
        size=100,
        step=50
    )

    # Build the search index
    index, documents = build_index(chunks)

    # Run the homework search query
    results = index.search("python function definition", num_results=5)

    # Print the top result dictionary
    print("Top result:")
    print(results[0])

    # Print only the source book/file
    print("\nTop result source:")
    print(results[0]["source"])