#!/bin/bash

set -e

cd "$(dirname "$0")/.."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

streamlit run streamlit_app.py --server.port 8501
