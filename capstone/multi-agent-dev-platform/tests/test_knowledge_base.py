from app.tools.knowledge_base import retrieve


def test_retrieve_returns_list():
    results = retrieve("service layer business logic", n_results=2)
    assert isinstance(results, list)

def test_retrieve_respects_n_results():
    results = retrieve("any query", n_results=2)
    assert len(results) <= 2

def test_retrieve_returns_strings():
    results = retrieve("input validation", n_results=1)
    assert all(isinstance(r, str) for r in results)

def test_retrieve_semantic_relevance():
    results = retrieve("route handler doing too much work", n_results=1)
    assert any("service" in r.lower() or "business" in r.lower() or "layer" in r.lower() for r in results)

def test_retrieve_different_queries_different_results():
    r1 = retrieve("database session management", n_results=1)
    r2 = retrieve("API input validation schema", n_results=1)
    assert r1 != r2
