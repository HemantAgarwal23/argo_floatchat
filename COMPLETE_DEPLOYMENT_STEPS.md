# 🚀 Complete ARGO FloatChat Deployment Steps

Follow this guide step-by-step to deploy your ARGO FloatChat application completely.

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] GitHub repository with your code pushed
- [ ] Groq API key (get from [console.groq.com](https://console.groq.com))
- [ ] Hugging Face API key (optional, for fallback)
- [ ] Email accounts for Render and Vercel

---

## 🔧 Step 1: Prepare Your Repository

### 1.1 Verify All Files Are Present
Check that these files exist in your repository:
```
argo_floatchat-main/
├── render.yaml
├── vercel.json
├── app.py
├── DEPLOYMENT.md
├── DEPLOYMENT_CHECKLIST.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   ├── env.example
│   └── setup_production.py
└── frontend/
    ├── frontend_config.py
    ├── floatchat_app.py
    └── env.example
```

### 1.2 Commit and Push to GitHub
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

---

## 🖥️ Step 2: Deploy Backend to Render

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with your GitHub account
4. Authorize Render to access your repositories

### 2.2 Create PostgreSQL Database
1. In Render dashboard, click **"New +"**
2. Select **"PostgreSQL"**
3. Configure the database:
   - **Name**: `argo-postgres`
   - **Database**: `argo_database`
   - **User**: `argo_user`
   - **Region**: Choose closest to your users
   - **Plan**: Starter (Free tier available)
4. Click **"Create Database"**
5. **IMPORTANT**: Copy and save these details:
   - External Database URL
   - Host
   - Port (usually 5432)
   - Database name
   - Username
   - Password

### 2.3 Create Web Service for Backend
1. In Render dashboard, click **"New +"**
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click **"Connect GitHub"**
   - Find and select your `argo_floatchat-main` repository
   - Click **"Connect"**
4. Configure the web service:
   - **Name**: `argo-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
   - **Plan**: Starter (Free tier available)

### 2.4 Set Environment Variables
In the web service configuration, add these environment variables:

**Required Variables:**
```
GROQ_API_KEY=your-groq-api-key-here
DB_HOST=your-postgres-host-from-render
DB_PORT=5432
DB_NAME=argo_database
DB_USER=argo_user
DB_PASSWORD=your-postgres-password-from-render
DEBUG=false
HOST=0.0.0.0
PORT=10000
```

**Optional Variables:**
```
HUGGINGFACE_API_KEY=your-huggingface-api-key
CHROMA_PERSIST_DIR=/opt/render/project/src/backend/data/vector_db
```

### 2.5 Deploy Backend
1. Click **"Create Web Service"**
2. Wait for deployment to complete (5-10 minutes)
3. Note your backend URL (e.g., `https://argo-backend.onrender.com`)

### 2.6 Test Backend Deployment
Test these endpoints:
```bash
# Health check
curl https://your-backend-url.onrender.com/health

# Database health
curl https://your-backend-url.onrender.com/health/database

# API info
curl https://your-backend-url.onrender.com/info
```

---

## 🎨 Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"**
3. Sign up with your GitHub account
4. Authorize Vercel to access your repositories

### 3.2 Create New Project
1. In Vercel dashboard, click **"New Project"**
2. Import your repository:
   - Find and select your `argo_floatchat-main` repository
   - Click **"Import"**
3. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: Leave empty (uses root)
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

### 3.3 Set Environment Variables
Before deploying, set these environment variables:

**Required Variables:**
```
BACKEND_URL=https://your-backend-url.onrender.com
BACKEND_TIMEOUT=30
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
```

### 3.4 Deploy Frontend
1. Click **"Deploy"**
2. Wait for deployment to complete (2-5 minutes)
3. Note your frontend URL (e.g., `https://your-project.vercel.app`)

### 3.5 Test Frontend Deployment
1. Visit your Vercel URL
2. Verify the page loads correctly
3. Test a sample query: "Show me temperature profiles in the Indian Ocean"

---

## 🔧 Step 4: Post-Deployment Setup

### 4.1 Initialize Backend Database
You need to set up the database after deployment:

**Option A: Using Render Shell (Recommended)**
1. Go to your Render web service dashboard
2. Click on **"Shell"** tab
3. Run these commands:
```bash
cd backend
python scripts/complete_setup.py
python scripts/setup_vector_db.py
```

**Option B: Using Render's Build Command**
1. Go to your web service settings
2. Update the build command to:
```bash
pip install -r requirements.txt && python scripts/complete_setup.py
```

### 4.2 Verify Database Setup
Test these endpoints to ensure database is working:
```bash
# Check database health
curl https://your-backend-url.onrender.com/health/database

# Check vector database
curl https://your-backend-url.onrender.com/health/vector-db

# Test a simple query
curl -X POST https://your-backend-url.onrender.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the system status?"}'
```

---

## 🧪 Step 5: End-to-End Testing

### 5.1 Frontend-Backend Integration Test
1. Open your Vercel frontend URL
2. Try these test queries:
   - "Show me temperature profiles in the Indian Ocean"
   - "What ARGO floats are available?"
   - "Display salinity data for the last month"

### 5.2 Feature Testing
Test these features:
- [ ] Natural language queries work
- [ ] Data visualizations display
- [ ] Maps show correctly
- [ ] Export functionality works
- [ ] Different oceanographic parameters are accessible

### 5.3 Performance Testing
- [ ] Pages load quickly (< 3 seconds)
- [ ] Queries respond in reasonable time (< 10 seconds)
- [ ] No timeout errors
- [ ] Visualizations render properly

---

## 🔍 Step 6: Troubleshooting Common Issues

### 6.1 Backend Issues

**Problem: Service keeps sleeping**
- **Solution**: Upgrade to paid plan or use Render's always-on option

**Problem: Database connection fails**
- **Check**: Environment variables are set correctly
- **Check**: Database service is running
- **Solution**: Verify database credentials

**Problem: Build fails**
- **Check**: All dependencies in requirements.txt
- **Check**: Python version compatibility
- **Solution**: Review build logs in Render dashboard

### 6.2 Frontend Issues

**Problem: Frontend can't connect to backend**
- **Check**: BACKEND_URL environment variable
- **Check**: CORS settings in backend
- **Solution**: Verify backend URL is correct and accessible

**Problem: Vercel deployment fails**
- **Check**: All files are in repository
- **Check**: vercel.json configuration
- **Solution**: Review Vercel function logs

### 6.3 Database Issues

**Problem: Database setup fails**
- **Check**: Database service is running
- **Check**: User has proper permissions
- **Solution**: Run setup scripts manually via shell

---

## 📊 Step 7: Monitoring and Maintenance

### 7.1 Set Up Monitoring
1. **Render Monitoring**:
   - Monitor service uptime
   - Check resource usage
   - Set up alerts for failures

2. **Vercel Monitoring**:
   - Monitor function executions
   - Check build success rates
   - Monitor bandwidth usage

### 7.2 Regular Maintenance
- Monitor API usage and costs
- Update dependencies regularly
- Backup database periodically
- Monitor performance metrics

---

## 🎉 Step 8: Go Live!

### 8.1 Final Verification
Before announcing your application:
- [ ] All health checks pass
- [ ] Sample queries work correctly
- [ ] Visualizations display properly
- [ ] No critical errors in logs
- [ ] Performance is acceptable

### 8.2 Share Your Application
- Share the Vercel URL with users
- Create documentation for end users
- Set up user feedback collection
- Monitor usage and performance

---

## 📞 Support Resources

If you encounter issues:

1. **Check Logs**:
   - Render: Go to your service → Logs tab
   - Vercel: Go to your project → Functions tab → View logs

2. **Documentation**:
   - [Render Docs](https://render.com/docs)
   - [Vercel Docs](https://vercel.com/docs)
   - [FastAPI Docs](https://fastapi.tiangolo.com/)
   - [Streamlit Docs](https://docs.streamlit.io/)

3. **Community Support**:
   - Render Community Forum
   - Vercel Community
   - Stack Overflow

---

## 🎯 Summary

After completing all steps, you should have:

✅ **Backend**: FastAPI service running on Render with PostgreSQL database
✅ **Frontend**: Streamlit app running on Vercel with global CDN
✅ **Database**: Properly initialized with ARGO data
✅ **AI Integration**: Groq API working for natural language processing
✅ **Monitoring**: Basic monitoring setup for both services

**Your ARGO FloatChat application is now live and accessible worldwide! 🌊**

---

*Need help? Refer to the troubleshooting section or check the detailed deployment guide in `DEPLOYMENT.md`*
