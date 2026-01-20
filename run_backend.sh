#!/bin/bash
# Run the FastAPI backend server
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
