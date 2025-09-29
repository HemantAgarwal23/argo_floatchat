#!/bin/bash

# ARGO FloatChat Deployment Script
# This script helps deploy the backend to Google Cloud Run

echo "🚀 ARGO FloatChat Deployment Script"
echo "=================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please login to Google Cloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set project (replace with your project ID)
PROJECT_ID="argo-floatchat"
REGION="us-central1"
SERVICE_NAME="argo-backend"

echo "📋 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🔧 Service: $SERVICE_NAME"
echo ""

# Navigate to backend directory
cd backend

echo "🔨 Building and deploying to Cloud Run..."
echo ""

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --port 8000 \
  --set-env-vars "HOST=0.0.0.0,PORT=8000" \
  --project $PROJECT_ID

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your backend URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID
echo ""
echo "📝 Next steps:"
echo "1. Set up your database (Cloud SQL)"
echo "2. Configure environment variables"
echo "3. Deploy frontend to Vercel"
echo "4. Update frontend BACKEND_URL"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
