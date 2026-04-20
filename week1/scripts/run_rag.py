# week1/scripts/run_rag.py

"""
Run the full RAG pipeline for the homework query.

What this script does:
1. Rebuilds chunks
2. Rebuilds the minsearch index
3. Runs the query: 'python function definition'
4. Prints:
   - top retrieved sources
   - final prompt length
   - answer
   - input tokens
   - output tokens
"""

from src.processing.chunking import chunk_all_documents
from src.indexing.build_index import build_index
from src.rag.rag_pipeline import rag


if __name__ == "__main__":
    # Recreate chunks from processed markdown files
    chunks = chunk_all_documents(
        input_dir="data/processed/",
        size=100,
        step=50
    )

    # Build index from chunks
    index, documents = build_index(chunks)

    # Homework query
    query = "python function definition"

    # Run full RAG
    result = rag(index, query)

    # Print retrieved sources first for debugging
    print("\nTop retrieved chunks came from:\n")
    for i, item in enumerate(result["search_results"], start=1):
        print(f"{i}. {item['source']}")

    # Print answer
    print("\nAnswer:\n")
    print(result["answer"])

    # Print token counts
    print("\nToken usage:\n")
    print(f"Input tokens: {result['input_tokens']}")
    print(f"Output tokens: {result['output_tokens']}")