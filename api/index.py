"""
Vercel serverless handler for Flask app
This file serves as the entry point for Vercel deployment
"""
import sys
import os
from pathlib import Path

# Add the Ani directory to Python path
project_root = Path(__file__).parent.parent
ani_path = project_root / 'Ani'
sys.path.insert(0, str(ani_path))

try:
    # Import the Flask app from app.py
    from app import app
    
    # Ensure the app is in production mode
    if os.environ.get('FLASK_ENV') != 'production':
        os.environ['FLASK_ENV'] = 'production'
    
    # Disable debug mode for serverless
    app.debug = False
    
except ImportError as e:
    print(f"Error importing Flask app: {e}")
    print(f"Python path: {sys.path}")
    print(f"Working directory: {os.getcwd()}")
    raise

# Vercel handler
# This app instance is what Vercel calls to handle requests

