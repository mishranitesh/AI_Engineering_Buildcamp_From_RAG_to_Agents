#!/bin/bash
set -e

if [ ! -f /app/knowledge_db/chroma.sqlite3 ]; then
    echo "First run: seeding knowledge base..."
    python seed_knowledge_base.py
    echo "Knowledge base ready."
fi

exec "$@"