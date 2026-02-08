"""
Vercel serverless handler for Flask app
This file serves as the entry point for Vercel deployment
"""
import sys
import os

# Add the Ani directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Ani'))

# Import the Flask app
from app import app

# Export the app for Vercel
# Vercel will use this app instance to handle requests
