#!/usr/bin/env python3
"""
Script to generate a secure SECRET_KEY for production use
Run this to get a secure key to use in your .env or Vercel environment variables
"""

import secrets

def generate_secret_key(length=32):
    """Generate a secure random secret key"""
    return secrets.token_hex(length)

if __name__ == '__main__':
    key = generate_secret_key()
    print("=" * 60)
    print("Generated Secure SECRET_KEY:")
    print("=" * 60)
    print(key)
    print("=" * 60)
    print("\nAdd this to your .env file or Vercel environment variables as:")
    print(f"SECRET_KEY={key}")
    print("=" * 60)
