#!/bin/bash
set -euo pipefail

echo "=== Agent System Local Setup ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required. Install Docker Desktop first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required."; exit 1; }

# Copy env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "  => Edit .env and set your LLM_API_KEY before proceeding!"
    exit 0
fi

# Start PostgreSQL
echo "Starting PostgreSQL..."
docker compose up -d postgres
echo "Waiting for PostgreSQL to be healthy..."
sleep 5

# Install Python dependencies (optional, for local dev)
if [ -d ".venv" ]; then
    echo "Virtual environment found, installing dependencies..."
    .venv/bin/pip install -r services/common/requirements.txt -q
else
    echo "No .venv found. Create one with: python3 -m venv .venv && source .venv/bin/activate"
fi

# Seed database
echo "Seeding database..."
python3 scripts/seed-db.py 2>/dev/null || echo "  (Seed skipped - DB may already have data)"

echo ""
echo "=== Setup Complete ==="
echo "Start all services: docker compose up -d"
echo "Or run individually: make dev"
