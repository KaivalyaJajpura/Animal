#!/usr/bin/env python3
"""Test the admin_user route logic directly"""
import sqlite3

def test_admin_user_logic():
    print("Testing admin_user route logic...")
    
    total_animals_treated = 0
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM treatment_history')
        result = cursor.fetchone()
        print(f"Query result: {result}")
        print(f"Result type: {type(result)}")
        
        if result is not None:
            total_animals_treated = result[0]
            print(f"Assigned to variable: {total_animals_treated}")
        
        conn.close()
        print(f"[ADMIN USER] Total animals treated: {total_animals_treated}")
        
        # Test what the template will see
        print(f"\nTemplate will display: {{ total_animals_treated | default(0) }} = {total_animals_treated if total_animals_treated is not None else 0}")
        
        return total_animals_treated
        
    except Exception as e:
        print(f"Error fetching total animals treated: {e}")
        import traceback
        traceback.print_exc()
        total_animals_treated = 0
        return total_animals_treated

if __name__ == "__main__":
    result = test_admin_user_logic()
    print(f"\n✓ Final result: {result}")
    if result == 9:
        print("✓✓ SUCCESS! The value is correct!")
    else:
        print(f"✗ FAILED! Expected 9, got {result}")
