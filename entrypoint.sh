#!/bin/sh

# Apply Alembic migrations
alembic upgrade head

# Run pytest
pytest

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
