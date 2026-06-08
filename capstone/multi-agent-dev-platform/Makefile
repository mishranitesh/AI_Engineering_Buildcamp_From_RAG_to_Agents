.PHONY: install seed api ui monitor test test-unit test-judge evaluate tune clean help

# ── Setup ─────────────────────────────────────────────────────────────────────

install:
	pip install uv
	uv venv .venv
	uv pip install -r requirements.txt

seed:
	.venv/bin/python seed_knowledge_base.py

# ── Run ───────────────────────────────────────────────────────────────────────

api:
	.venv/bin/uvicorn app.main:app --reload --reload-dir app

ui:
	.venv/bin/streamlit run ui/streamlit_app.py

monitor:
	.venv/bin/streamlit run ui/monitoring.py --server.port 8502

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-unit test-judge

test-unit:
	.venv/bin/pytest tests/test_parsers.py tests/test_state.py \
		tests/test_generators.py tests/test_knowledge_base.py \
		tests/test_tools_mocked.py -v

test-judge:
	.venv/bin/pytest tests/test_judge.py -v

# ── Evaluation ────────────────────────────────────────────────────────────────

evaluate:
	.venv/bin/python -m evaluation.run_evaluation

tune:
	.venv/bin/python -m evaluation.tune_parameters

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf logs/workflow.log
	rm -rf generated_projects/
	rm -rf __pycache__ app/**/__pycache__ app/**/**/__pycache__
	rm -rf .pytest_cache

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo "Available commands:"
	@echo "  make install     - Install uv and dependencies"
	@echo "  make seed        - Seed the knowledge base"
	@echo "  make api         - Start FastAPI server (port 8000)"
	@echo "  make ui          - Start main Streamlit UI (port 8501)"
	@echo "  make monitor     - Start monitoring dashboard (port 8502)"
	@echo "  make test        - Run all tests (unit + judge)"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-judge  - Run LLM judge tests only"
	@echo "  make evaluate    - Run ground truth evaluation"
	@echo "  make tune        - Run parameter tuning"
	@echo "  make clean       - Remove logs, generated projects, cache"
