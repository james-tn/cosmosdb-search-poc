#!/usr/bin/env bash
# Launch the Cosmos DB search POC UI.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and fill in your Azure resource details." >&2
  exit 1
fi

# Authenticate first with: az login
exec python3 -m streamlit run app.py "$@"
