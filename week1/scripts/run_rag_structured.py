"""
Run the structured-output version of the homework RAG pipeline.

This script:
1. Builds chunks
2. Builds the minsearch index
3. Runs the query with structured output
4. Prints the parsed result
5. Prints token usage
"""

from src.processing.chunking import chunk_all_documents
from src.indexing.build_index import build_index
from src.rag.rag_pipeline import rag_structured


if __name__ == "__main__":
    # Rebuild chunks from markdown books
    chunks = chunk_all_documents(
        input_dir="data/processed/",
        size=100,
        step=50
    )

    # Build the minsearch index
    index, documents = build_index(chunks)

    # Homework query
    query = "python function definition"

    # Run structured RAG
    result = rag_structured(index, query)

    # Print the structured object
    print("\nStructured answer:\n")
    print(result["structured_answer"])

    # Print token usage
    print("\nToken usage:\n")
    print(f"Input tokens: {result['input_tokens']}")
    print(f"Output tokens: {result['output_tokens']}")