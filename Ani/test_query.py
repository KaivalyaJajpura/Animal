#!/usr/bin/env python3
import sqlite3
import sys

try:
    print("Testing database connection...")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Test the exact query
    cursor.execute('SELECT COUNT(*) FROM treatment_history')
    result = cursor.fetchone()
    
    print(f"Query result: {result}")
    print(f"Result type: {type(result)}")
    print(f"Result[0]: {result[0]}")
    
    if result and result[0]:
        total = result[0]
        print(f"Total animals treated (using if result and result[0]): {total}")
    else:
        print("Condition failed - would default to 0")
    
    conn.close()
    print("✓ Database test successful!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
