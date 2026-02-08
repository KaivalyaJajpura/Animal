#!/usr/bin/env python3
"""
Fix all database path references in app.py
"""

import os

script_dir = os.path.dirname(__file__)
app_file = os.path.join(script_dir, 'Ani', 'app.py')

print(f"Processing: {app_file}")

with open(app_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Count replacements before
before_count = content.count("sqlite3.connect('users.db')")
before_count += content.count('sqlite3.connect("users.db")')

# Replace all database path references
content = content.replace("sqlite3.connect('users.db')", 'sqlite3.connect(DB_PATH)')
content = content.replace('sqlite3.connect("users.db")', 'sqlite3.connect(DB_PATH)')
content = content.replace("open('schema.sql')", "open(schema_path)")
content = content.replace('open("schema.sql")', "open(schema_path)")
content = content.replace("open('last_reading_time.txt')", "open(os.path.join(os.path.dirname(DB_PATH), 'last_reading_time.txt'))")

# Write back
with open(app_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ Updated {before_count} database path references")
print("✓ Fix completed successfully!")
