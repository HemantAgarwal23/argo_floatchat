# 🚀 ARGO FloatChat Deployment Guide

This guide will help you deploy the ARGO FloatChat application with:
- **Backend**: Deployed on Render.com
- **Frontend**: Deployed on Vercel.com

## 📋 Prerequisites

Before deploying, ensure you have:

1. **GitHub Repository**: Your code pushed to GitHub
2. **API Keys**: 
   - Groq API key (required)
   - Hugging Face API key (optional, for fallback)
3. **Database**: PostgreSQL database (can be provisioned through Render)

## 🔧 Backend Deployment (Render)

### Step 1: Prepare Your Repository

1. Ensure your code is pushed to GitHub
2. The following files should be present in your repository:
   - `render.yaml` (Render configuration)
   - `backend/Dockerfile` (Container configuration)
   - `backend/requirements.txt` (Dependencies)
   - `backend/run.py` (Application entry point)

### Step 2: Create Render Account and Connect Repository

1. Go to [render.com](https://render.com) and sign up
2. Connect your GitHub account
3. Import your repository

### Step 3: Deploy PostgreSQL Database

1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - **Name**: `argo-postgres`
   - **Database**: `argo_database`
   - **User**: `argo_user`
   - **Plan**: Starter (free tier available)
4. Note down the connection details

### Step 4: Deploy Backend Service

1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your repository
4. Configure the service:
   - **Name**: `argo-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`

### Step 5: Configure Environment Variables

In the Render dashboard, go to your backend service and add these environment variables:

```bash
# Required
GROQ_API_KEY=your-groq-api-key-here
DB_HOST=your-postgres-host-from-render
DB_PORT=5432
DB_NAME=argo_database
DB_USER=argo_user
DB_PASSWORD=your-postgres-password-from-render

# Optional
HUGGINGFACE_API_KEY=your-huggingface-api-key
DEBUG=false
HOST=0.0.0.0
PORT=10000
CHROMA_PERSIST_DIR=/opt/render/project/src/backend/data/vector_db
```

### Step 6: Deploy and Test

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Test your backend: `https://your-service-name.onrender.com/health`
4. Note the backend URL for frontend configuration

## 🎨 Frontend Deployment (Vercel)

### Step 1: Prepare Frontend Configuration

1. Update `frontend/frontend_config.py` to use your Render backend URL
2. Ensure `vercel.json` is in your repository root

### Step 2: Create Vercel Account and Connect Repository

1. Go to [vercel.com](https://vercel.com) and sign up
2. Connect your GitHub account
3. Import your repository

### Step 3: Configure Vercel Project

1. In Vercel dashboard, click "New Project"
2. Select your repository
3. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty (uses root)
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty

### Step 4: Set Environment Variables

In Vercel dashboard, go to your project settings and add:

```bash
BACKEND_URL=https://your-render-backend-url.onrender.com
BACKEND_TIMEOUT=30
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
```

### Step 5: Deploy and Test

1. Click "Deploy"
2. Wait for deployment to complete
3. Test your frontend at the provided Vercel URL
4. Verify the frontend can communicate with the backend

## 🔍 Post-Deployment Setup

### Backend Database Setup

After your backend is deployed, you need to set up the database:

1. SSH into your Render service or use Render's shell
2. Run the database setup scripts:

```bash
cd backend
python scripts/complete_setup.py
```

### Vector Database Setup

Set up the vector database for semantic search:

```bash
cd backend
python scripts/setup_vector_db.py
```

## 🧪 Testing Your Deployment

### Backend Health Checks

```bash
# Overall health
curl https://your-backend-url.onrender.com/health

# Database health
curl https://your-backend-url.onrender.com/health/database

# Vector database health
curl https://your-backend-url.onrender.com/health/vector-db
```

### Frontend Testing

1. Visit your Vercel URL
2. Try a sample query: "Show me temperature profiles in the Indian Ocean"
3. Verify visualizations are working
4. Test different oceanographic parameters

## 🔧 Troubleshooting

### Common Issues

1. **Backend Connection Timeout**
   - Check if backend is running: `https://your-backend.onrender.com/health`
   - Verify environment variables are set correctly
   - Check Render logs for errors

2. **Database Connection Issues**
   - Verify PostgreSQL service is running
   - Check database credentials in environment variables
   - Ensure database exists and user has proper permissions

3. **Vector Database Empty**
   - Run the vector database setup script
   - Check if data files are present in the backend

4. **Frontend Not Loading**
   - Check Vercel deployment logs
   - Verify `BACKEND_URL` environment variable
   - Ensure CORS is configured correctly in backend

### Render Service Issues

- Check Render dashboard for service logs
- Verify all environment variables are set
- Ensure the service is not sleeping (free tier limitation)

### Vercel Issues

- Check Vercel function logs
- Verify environment variables in project settings
- Ensure all dependencies are properly installed

## 📊 Monitoring and Maintenance

### Render Monitoring

- Monitor service uptime in Render dashboard
- Set up alerts for service failures
- Monitor resource usage and upgrade if needed

### Vercel Monitoring

- Monitor function execution in Vercel dashboard
- Check for any build or runtime errors
- Monitor bandwidth usage

## 🔄 Updating Your Deployment

### Backend Updates

1. Push changes to your GitHub repository
2. Render will automatically redeploy
3. Test the updated backend

### Frontend Updates

1. Push changes to your GitHub repository
2. Vercel will automatically redeploy
3. Test the updated frontend

## 💰 Cost Considerations

### Render (Backend)

- **Free Tier**: 750 hours/month for web services
- **Starter Plan**: $7/month for always-on service
- **PostgreSQL**: Free tier available with limitations

### Vercel (Frontend)

- **Free Tier**: 100GB bandwidth, 1000 serverless function executions
- **Pro Plan**: $20/month for unlimited bandwidth and executions

## 🎯 Production Considerations

### Security

1. **Environment Variables**: Never commit API keys to repository
2. **CORS**: Configure proper CORS origins in production
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **HTTPS**: Both Render and Vercel provide HTTPS by default

### Performance

1. **Database Indexing**: Ensure proper database indexes
2. **Caching**: Implement caching for frequently accessed data
3. **CDN**: Vercel provides global CDN automatically
4. **Monitoring**: Set up proper monitoring and alerting

### Scalability

1. **Database**: Consider upgrading to paid PostgreSQL plans for better performance
2. **Backend**: Upgrade Render service plan for more resources
3. **Caching**: Implement Redis for session and data caching

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Render and Vercel documentation
3. Check application logs in both platforms
4. Verify all environment variables are correctly set

---

**Happy Deploying! 🌊**

Your ARGO FloatChat application should now be live and accessible to users worldwide!
