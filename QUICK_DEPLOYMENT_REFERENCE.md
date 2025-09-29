# ⚡ Quick Deployment Reference

## 🚀 Essential Steps Summary

### 1. Get API Keys
- **Groq API**: [console.groq.com](https://console.groq.com) → Get API Key
- **Hugging Face**: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (optional)

### 2. Backend (Render)
1. **Sign up**: [render.com](https://render.com) → GitHub login
2. **Create Database**: New → PostgreSQL → Name: `argo-postgres`
3. **Create Web Service**: New → Web Service → Connect repo → Root: `backend`
4. **Environment Variables**:
   ```
   GROQ_API_KEY=your-key
   DB_HOST=your-postgres-host
   DB_PASSWORD=your-password
   DEBUG=false
   HOST=0.0.0.0
   PORT=10000
   ```
5. **Deploy** → Note backend URL

### 3. Frontend (Vercel)
1. **Sign up**: [vercel.com](https://vercel.com) → GitHub login
2. **New Project**: Import repo → Framework: Other
3. **Environment Variables**:
   ```
   BACKEND_URL=https://your-backend.onrender.com
   ```
4. **Deploy** → Note frontend URL

### 4. Setup Database
- **Render Shell**: Go to service → Shell tab
- **Run**: `cd backend && python scripts/complete_setup.py`

### 5. Test
- **Backend**: `https://your-backend.onrender.com/health`
- **Frontend**: Visit Vercel URL → Try query: "Show me temperature profiles"

---

## 🔑 Critical URLs to Save

- **Backend URL**: `https://argo-backend.onrender.com`
- **Frontend URL**: `https://your-project.vercel.app`
- **Database URL**: From Render PostgreSQL service
- **API Docs**: `https://your-backend.onrender.com/docs`

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend sleeping | Upgrade to paid plan |
| Database connection failed | Check environment variables |
| Frontend can't connect | Verify BACKEND_URL |
| Build fails | Check requirements.txt |

---

## 📞 Emergency Contacts

- **Render Support**: [render.com/docs](https://render.com/docs)
- **Vercel Support**: [vercel.com/docs](https://vercel.com/docs)
- **Project Docs**: Check `DEPLOYMENT.md`

---

**⏱️ Total Time**: ~30-45 minutes
**💰 Cost**: Free tier available for both platforms
