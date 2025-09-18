#!/bin/bash

set -e

echo "🌊 Starting FloatChat Frontend..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v ^# | xargs)
fi

# Create directories
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "floatchat-frontend-env" ]; then
    source floatchat-frontend-env/bin/activate
fi

# Check backend connectivity
echo "🔍 Checking backend connectivity..."
if curl -f -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Backend is accessible at $BACKEND_URL"
else
    echo "⚠️  Backend not accessible - some features may be limited"
fi

# Start production server
echo "🚀 Starting production server..."
streamlit run floatchat_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    2>&1 | tee logs/frontend.log