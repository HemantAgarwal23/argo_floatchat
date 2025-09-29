# 🚀 ARGO FloatChat Deployment Guide

## 📋 Overview

This guide will help you deploy:
- **Backend**: Google Cloud Run (FastAPI)
- **Frontend**: Vercel (Streamlit)
- **Database**: Google Cloud SQL (PostgreSQL)

## 🎯 Prerequisites

1. **Google Cloud Account** (get $300 free credit)
2. **Vercel Account** (free)
3. **GitHub Repository** (your code)
4. **API Keys**: Groq API key (required)

## 🔧 Backend Deployment (Google Cloud Run)

### Step 1: Google Cloud Setup

1. **Create Google Cloud Project**
   ```bash
   # Install Google Cloud CLI
   # Visit: https://cloud.google.com/sdk/docs/install
   
   # Login to Google Cloud
   gcloud auth login
   
   # Create new project
   gcloud projects create argo-floatchat --name="ARGO FloatChat"
   
   # Set project
   gcloud config set project argo-floatchat
   ```

2. **Enable Required APIs**
   ```bash
   # Enable Cloud Run API
   gcloud services enable run.googleapis.com
   
   # Enable Cloud Build API
   gcloud services enable cloudbuild.googleapis.com
   
   # Enable Cloud SQL API
   gcloud services enable sqladmin.googleapis.com
   ```

### Step 2: Create Cloud SQL Database

1. **Create PostgreSQL Instance**
   ```bash
   # Create Cloud SQL instance
   gcloud sql instances create argo-postgres \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1 \
     --root-password=your-secure-password
   ```

2. **Create Database and User**
   ```bash
   # Create database
   gcloud sql databases create argo_database --instance=argo-postgres
   
   # Create user
   gcloud sql users create argo_user --instance=argo-postgres --password=your-user-password
   ```

### Step 3: Deploy Backend to Cloud Run

1. **Build and Deploy**
   ```bash
   # Navigate to backend directory
   cd backend
   
   # Build and deploy to Cloud Run
   gcloud run deploy argo-backend \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2 \
     --port 8000 \
     --set-env-vars "HOST=0.0.0.0,PORT=8000,DB_HOST=your-cloud-sql-ip,DB_PASSWORD=your-password,GROQ_API_KEY=your-groq-key"
   ```

2. **Get Backend URL**
   - Note the service URL (e.g., `https://argo-backend-xxx.run.app`)

## 🎨 Frontend Deployment (Vercel)

### Step 1: Vercel Setup

1. **Connect GitHub Repository**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub
   - Import your repository

2. **Configure Project**
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty

### Step 2: Set Environment Variables

In Vercel dashboard, add these environment variables:
```
BACKEND_URL=https://your-cloud-run-url.run.app
BACKEND_TIMEOUT=30
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
```

### Step 3: Deploy

1. **Deploy Frontend**
   - Click "Deploy"
   - Wait for deployment to complete
   - Note the frontend URL

## 🔍 Post-Deployment Setup

### Backend Database Setup

1. **SSH into Cloud Run** (or use Cloud Shell)
   ```bash
   # Install dependencies and run setup
   cd backend
   pip install -r requirements.txt
   python scripts/complete_setup.py
   ```

2. **Set up Vector Database**
   ```bash
   python scripts/setup_vector_db.py
   ```

## 🧪 Testing Your Deployment

### Backend Health Checks
```bash
# Overall health
curl https://your-backend-url.run.app/health

# Database health
curl https://your-backend-url.run.app/health/database

# Vector database health
curl https://your-backend-url.run.app/health/vector-db
```

### Frontend Testing
1. Visit your Vercel URL
2. Try a sample query: "Show me temperature profiles in the Indian Ocean"
3. Verify visualizations are working

## 💰 Cost Breakdown

| Component | Platform | First 90 Days | After 90 Days |
|-----------|----------|---------------|---------------|
| **Backend** | Google Cloud Run | **$0** (free credit) | $15-25/month |
| **Frontend** | Vercel | **$0** (always free) | **$0** (always free) |
| **Database** | Cloud SQL | **$0** (free credit) | $15-25/month |
| **Total** | | **$0** | $15-25/month |

## 🔧 Troubleshooting

### Common Issues

1. **Backend Connection Timeout**
   - Check if backend is running: `https://your-backend.run.app/health`
   - Verify environment variables are set correctly
   - Check Cloud Run logs

2. **Database Connection Issues**
   - Verify Cloud SQL instance is running
   - Check database credentials in environment variables
   - Ensure database exists and user has proper permissions

3. **Frontend Not Loading**
   - Check Vercel deployment logs
   - Verify `BACKEND_URL` environment variable
   - Ensure CORS is configured correctly in backend

## 🎯 Next Steps

After successful deployment:
1. **Monitor usage** to stay within free limits
2. **Set up monitoring** and alerts
3. **Plan for post-90-day** costs
4. **Consider migrating** to Railway ($5/month) if needed

---

**Happy Deploying! 🌊**

Your ARGO FloatChat application should now be live and accessible worldwide!
