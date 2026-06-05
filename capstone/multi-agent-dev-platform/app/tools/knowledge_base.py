import chromadb
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma = chromadb.PersistentClient(path="./knowledge_db")
collection = chroma.get_or_create_collection("code_patterns")

def embed(text: str) -> list[float]:
    return client.embeddings.create(
        input=text, model="text-embedding-3-small"
    ).data[0].embedding

def add_document(doc_id: str, text: str, metadata: dict = {}):
    collection.upsert(
        ids=[doc_id],
        embeddings=[embed(text)],
        documents=[text],
        metadatas=[metadata],
    )

def retrieve(query: str, n_results: int = 3) -> list[str]:
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=n_results,
    )
    return results["documents"][0]
