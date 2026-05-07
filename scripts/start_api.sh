#!/bin/bash

# Quick-start script for the ChatBI API
# Usage: bash scripts/start_api.sh (run from the chatbi-application/ repo root)

set -e

# Switch to the project root
cd "$(dirname "$0")/.."

# Color output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ChatBI API Launch Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Check Python
echo -e "${YELLOW}[1/5] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# Check the virtual environment
echo -e "${YELLOW}[2/5] Checking virtual environment...${NC}"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Install dependencies
echo -e "${YELLOW}[3/5] Installing dependencies...${NC}"
pip install -q -r requirements-api.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check environment variables
echo -e "${YELLOW}[4/5] Checking environment variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}  -> .env not found, copying from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}  Please edit .env and set DEEPSEEK_API_KEY${NC}"
    else
        echo -e "${YELLOW}  -> Creating .env file...${NC}"
        cat > .env << EOF
DEEPSEEK_API_KEY=
API_HOST=0.0.0.0
API_PORT=8000
EOF
        echo -e "${YELLOW}  Please edit .env and set DEEPSEEK_API_KEY${NC}"
    fi
fi

# Load environment variables
set -a
source .env
set +a

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}  Warning: DEEPSEEK_API_KEY is not set${NC}"
fi
echo -e "${GREEN}✓ Environment variables loaded${NC}"

# Start the API
echo -e "${YELLOW}[5/5] Starting the API service...${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}ChatBI API is running at: http://localhost:8000${NC}"
echo -e "${GREEN}API docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Press CTRL+C to stop the service${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""

uvicorn api:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload
