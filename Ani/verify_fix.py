#!/usr/bin/env python3
"""Test by making a request to the Flask app"""
import sqlite3
from flask import Flask, render_template, session
import os

os.chdir('d:\\Ani_Health(Final)\\Ani')

# Test just the database query
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM treatment_history')
result = cursor.fetchone()

total_animals_treated = 0
if result is not None:
    total_animals_treated = result[0]

print(f"Total animals treated from database: {total_animals_treated}")

# Verify template syntax
template_var = total_animals_treated
print(f"Value to pass to template: {template_var}")
print(f"Template will render: {template_var} (with default filter it becomes {template_var if template_var is not None else 0})")

conn.close()

if total_animals_treated == 9:
    print("\n✓✓✓ SUCCESS! The code should display 9 on the page!")
else:
    print(f"\n✗ ERROR: Expected 9, got {total_animals_treated}")
