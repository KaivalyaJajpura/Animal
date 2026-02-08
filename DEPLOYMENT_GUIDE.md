# Vercel Deployment Guide

Complete step-by-step guide to deploy your Ani Health Flask app to Vercel.

## Quick Start (5 minutes)

### Step 1: Generate a Secure Secret Key

Run this command in your terminal:
```bash
python generate_key.py
```
Copy the generated key - you'll need it soon.

### Step 2: Push Code to GitHub

Make sure your code is pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### Step 3: Connect to Vercel

1. Visit https://vercel.com
2. Sign up/log in with your GitHub account
3. Click "New Project"
4. Select your `Animal` repository
5. Click "Import"

### Step 4: Configure Environment

In the "Environment Variables" section, add:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Paste your generated key |

### Step 5: Deploy!

Click "Deploy" and wait for deployment to complete.

Your app will be live at: `https://your-project-name.vercel.app`

---

## Detailed Configuration

### Project Root Settings

The deployment should detect:
- **Framework**: Python
- **Build Command**: (Auto-detected from vercel.json)
- **Output Directory**: (Not needed for Python)

### vercel.json Breakdown

```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "Ani/Static/$1" },
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

This configuration:
- Uses `api/index.py` as the serverless function handler
- Routes static files from `Ani/Static/` folder
- Routes all other requests to the Flask app

---

## What's Different on Vercel

### ✅ What Works
- All web routes and pages
- User authentication
- Database operations (with limitations)
- File uploads (temporary storage only)
- API endpoints
- ML model predictions (with cold start delay)

### ⚠️ Limitations

#### 1. Background Scheduler
The health reading scheduler (every 5 minutes) is **disabled** in production because:
- Vercel serverless functions don't run continuously
- Each request spins up a new container

**Workarounds:**
- Use Vercel Cron Jobs (paid feature)
- Use external service: AWS Lambda, Google Cloud Functions
- Use a separate background job service

#### 2. Database
SQLite has issues in serverless environment:
- File locking problems
- Data persistence between requests

**Recommended:** Use PostgreSQL
```bash
# Install pg8000
pip install pg8000

# Update requirements.txt
echo "pg8000==1.30.3" >> requirements.txt
```

Then update your database connection:
```python
import os
db_url = os.getenv('DATABASE_URL', 'sqlite:///users.db')
# Use SQLAlchemy or direct psycopg2 connection
```

#### 3. File Storage
Temporary files won't persist between requests.

**Solution:** Use cloud storage
- Vercel Postgres File Storage
- AWS S3
- Google Cloud Storage
- Cloudinary (for images)

---

## Environment Variables Reference

### Required
- `FLASK_ENV`: Must be `production`
- `SECRET_KEY`: A secure random key (generate with `generate_key.py`)

### Optional
- `DATABASE_URL`: If using PostgreSQL instead of SQLite
- `FLASK_DEBUG`: Set to `False` for production
- `MAX_CONTENT_LENGTH`: Max upload size in bytes

---

## Verification Checklist

After deployment, verify:

- [ ] Homepage loads: `https://your-app.vercel.app`
- [ ] Login page accessible: `https://your-app.vercel.app/login`
- [ ] CSS/JS files load correctly (check browser console)
- [ ] Database operations work (add a test user)
- [ ] Model predictions work (upload an image if applicable)
- [ ] No 500 errors in Vercel logs

### Check Logs

View deployment logs:
1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments" → Latest deployment
4. View "Logs" tab

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Check `api/index.py` Python path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Ani'))
```

### Issue: Static files not loading

**Check:** 
1. Files are in `Ani/Static/` folder
2. Routes in `vercel.json` are correct
3. Clear browser cache with Ctrl+Shift+Delete

### Issue: Database errors

**Solution:** 
1. Check file permissions
2. Use cloud database instead of SQLite
3. Verify database path is correct

### Issue: Model loading takes too long

**Cause:** TensorFlow initialization is slow on cold start (first request)
**Solution:** 
1. Use Vercel Pro (longer timeout)
2. Optimize model loading (lazy loading)
3. Use a smaller model

### Issue: 500 Internal Server Error

**Debug steps:**
1. Check Vercel deployment logs
2. Check environment variables are set
3. Check all imports can be resolved
4. Test locally with `vercel dev`

---

## Alternative Deployment Options

If Vercel doesn't work for your needs:

### Heroku (with Procfile)
```bash
heroku create your-app-name
git push heroku main
heroku config:set SECRET_KEY=your_key
```

### Railway (Railway.app)
1. Connect GitHub repo
2. Add environment variables
3. Deploy (uses Procfile automatically)

### PythonAnywhere
1. Upload code
2. Configure WSGI
3. Set up virtual environment
4. Reload web app

### AWS (EC2 + RDS)
More control but more complex:
- EC2 for Flask app
- RDS for database
- S3 for file storage

---

## Security Best Practices

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Never commit `.env` file to git
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (Vercel does by default)
- [ ] Validate all user inputs
- [ ] Keep dependencies updated
- [ ] Use strong passwords for admin accounts
- [ ] Enable CORS only for trusted domains
- [ ] Regularly update Flask and dependencies

---

## Performance Tips

1. **Lazy load ML models** - Load only when needed
2. **Cache static assets** - Vercel does this automatically
3. **Optimize images** - Compress before upload
4. **Use CDN** - Vercel includes this
5. **Database indexing** - Index frequently queried fields
6. **Async operations** - Use for long-running tasks

---

## Monitoring & Logs

In Vercel Dashboard:
- Real-time logs
- Error tracking
- Performance metrics
- Deployment history

Sign up for better monitoring:
- Sentry (error tracking)
- LogRocket (session replay)
- DataDog (APM)

---

## Getting Help

- Vercel Docs: https://vercel.com/docs
- Flask Docs: https://flask.palletsprojects.com
- GitHub Issues: Report bugs in repository
- Stack Overflow: Tag with `vercel` + `flask`

---

## After Deployment

1. **Test all features** in production
2. **Monitor for errors** in the logs
3. **Get a custom domain** (optional)
4. **Set up error alerts**
5. **Plan for database migration** if using SQLite
6. **Schedule regular backups**
7. **Keep code updated** on main branch

Good luck! 🚀
