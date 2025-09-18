#!/bin/bash

set -e

echo "🔧 Starting FloatChat in Development Mode..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v ^# | xargs)
fi

# Create necessary directories
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "floatchat-frontend-env" ]; then
    source floatchat-frontend-env/bin/activate
fi

# Set development environment
export DEBUG_MODE=true
export STREAMLIT_SERVER_HEADLESS=false
export LOG_LEVEL=DEBUG

# Check backend connectivity
echo "🔍 Checking backend connectivity..."
if curl -f -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Backend is accessible at $BACKEND_URL"
else
    echo "⚠️  Backend not accessible - running in demo mode"
fi

# Start development server
echo "🚀 Starting development server on port 8501..."
streamlit run floatchat_app.py \
    --server.port=8501 \
    --server.address=localhost \
    --server.headless=false \
    --server.runOnSave=true