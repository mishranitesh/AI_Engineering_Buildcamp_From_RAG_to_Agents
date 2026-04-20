import os
from gitsource import chunk_documents


def prepare_documents(input_dir: str):
    """
    Read all markdown files from a directory and prepare them
    in the format expected before chunking.

    Parameters
    ----------
    input_dir : str
        Directory containing markdown (.md) files.

    Returns
    -------
    list[dict]
        A list of dictionaries where each dictionary represents one book:
        {
            "source": <filename>,
            "content": [list of non-empty lines]
        }
    """

    documents = []

    # Loop through all files in the input directory
    for filename in os.listdir(input_dir):
        # Only process markdown files
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(input_dir, filename)

        # Open markdown file and read all text
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Split full text into individual lines
        lines = text.splitlines()

        # Remove empty lines and lines that contain only whitespace
        cleaned_lines = [line.strip() for line in lines if line.strip()]

        # Store one document per file
        documents.append({
            "source": filename,
            "content": cleaned_lines
        })

    return documents


def chunk_all_documents(input_dir: str, size: int = 100, step: int = 50):
    """
    Prepare markdown documents and chunk them using gitsource.

    Parameters
    ----------
    input_dir : str
        Directory containing markdown files.

    size : int
        Number of lines/items per chunk.

    step : int
        Sliding window step size.

    Returns
    -------
    list[dict]
        Chunked documents.
    """

    # Prepare documents first
    documents = prepare_documents(input_dir)

    # Apply chunking with sliding window
    chunks = chunk_documents(documents, size=size, step=step)

    return chunks