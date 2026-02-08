# Ani Health - Animal Health Management System

A Flask-based web application for managing animal health records, using AI/ML for health predictions.

## Setup Instructions

### Local Development

1. **Clone the repository:**
   ```
   git clone https://github.com/KaivalyaJajpura/Animal.git
   cd Animal
   ```

2. **Create a virtual environment:**
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```
   python Ani/app.py
   ```

   The app will be available at `http://localhost:5000`

---

## Vercel Deployment

### Prerequisites

1. **Vercel Account**: Create one at https://vercel.com
2. **GitHub Account**: Push your code to GitHub
3. **Vercel CLI** (optional): `npm install -g vercel`

### Deployment Steps

#### Option 1: Deploy via Vercel Dashboard (Recommended)

1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Import your GitHub repository
4. Configure project settings:
   - **Framework Preset**: Python
   - **Root Directory**: (leave as default)
   - **Build Command**: (leave empty - uses vercel.json)
   - **Output Directory**: (leave empty)

5. Add Environment Variables in Vercel Dashboard:
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-a-secure-random-key>
   ```

6. Click "Deploy"

#### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from your project directory
vercel

# For production deployment
vercel --prod
```

### Environment Variables for Vercel

Set these in your Vercel Project Settings → Environment Variables:

- `FLASK_ENV`: Set to `production`
- `SECRET_KEY`: A secure random string (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `FLASK_DEBUG`: Set to `False` for production

### Important Notes for Serverless Deployment

⚠️ **Known Limitations on Vercel:**

1. **Background Scheduler**: The APScheduler that runs every 5 minutes is disabled in production/serverless mode. Consider using:
   - Vercel Cron Jobs (Pro plan)
   - External services like AWS Lambda, Google Cloud Functions
   - A dedicated background job service

2. **Database**: SQLite has limitations in serverless. For production, consider:
   - PostgreSQL (via Vercel Postgres)
   - MongoDB Atlas
   - Other cloud databases

3. **File Storage**: Temporary files may not persist between requests. Use cloud storage for file uploads.

4. **Cold Starts**: Initial ML model loading may take longer on first request.

---

## Directory Structure

```
Ani_Health/
├── api/
│   └── index.py                 # Serverless handler for Vercel
├── Ani/
│   ├── Templates/               # Flask HTML templates
│   ├── Static/                  # CSS, JS, images
│   │   ├── Css/
│   │   └── JS/
│   ├── Model/                   # ML model files
│   │   ├── keras_model.h5
│   │   └── labels.txt
│   ├── app.py                   # Main Flask application
│   ├── login.py                 # Authentication logic
│   ├── admin.py                 # Admin management
│   ├── user.py                  # User management
│   ├── simulate.py              # Health data simulation
│   ├── users.db                 # SQLite database
│   └── ...
├── requirements.txt             # Python dependencies
├── vercel.json                  # Vercel configuration
├── .vercelignore               # Files to exclude from deployment
├── .env.example                # Environment variable template
└── README.md                   # This file
```

---

## Features

- User authentication (regular users, veterinarians, admins)
- Animal health monitoring with real-time data
- AI-powered health predictions using Keras/TensorFlow
- Health history tracking and analytics
- Export functionality (Excel, CSV)
- Multi-language support (i18n)
- Responsive dashboard for all user types

---

## Local Testing

### Test the Vercel configuration locally

```bash
# Install Vercel CLI
npm install -g vercel

# Run locally (simulates Vercel environment)
vercel dev
```

---

## Troubleshooting

### Import Errors
- Make sure `api/index.py` can find the Ani module
- Check Python path configuration in `api/index.py`

### Database Issues
- SQLite may have file locking issues in serverless
- Consider migrating to PostgreSQL or MongoDB

### Model Loading Issues
- TensorFlow/Keras can be slow to load (large dependencies)
- Cold starts may time out on free tier
- Consider using Vercel Pro for longer timeout limits

### Static Files Not Loading
- Verify `vercel.json` routes configuration
- Ensure files are in `Ani/Static/` directory

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Configure a proper database (not SQLite)
- [ ] Set up environment variables on Vercel
- [ ] Test all features in production
- [ ] Set up monitoring and error tracking
- [ ] Configure custom domain (if desired)
- [ ] Set up CI/CD for automated deployments
- [ ] Review security settings and CORS

---

## Support & Issues

For bugs and feature requests, please open an issue on GitHub.

---

## License

[Your License Here]
