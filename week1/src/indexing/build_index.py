from minsearch import Index


def prepare_chunks_for_indexing(chunks):
    """
    Convert chunk content from list of lines → single string.

    Parameters
    ----------
    chunks : list[dict]
        Output from chunk_documents()

    Returns
    -------
    list[dict]
        Documents ready for indexing
    """

    documents = []

    for chunk in chunks:
        # Convert list of lines into a single string
        content_str = "\n".join(chunk["content"])

        documents.append({
            "source": chunk["source"],
            "content": content_str
        })

    return documents


def build_index(chunks):
    """
    Build a search index using minsearch.

    Parameters
    ----------
    chunks : list[dict]

    Returns
    -------
    Index
    """

    # Prepare documents - Convert chunks → indexable documents
    documents = prepare_chunks_for_indexing(chunks)

    # Create index - specify which fields are searchable text
    index = Index(text_fields=["content"])

    # Fit index on documents
    index.fit(documents)

    return index, documents