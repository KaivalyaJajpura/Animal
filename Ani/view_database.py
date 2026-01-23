#!/usr/bin/env python3
"""Script to view database contents"""
import sqlite3

def view_users_db():
    print("=" * 80)
    print("USERS DATABASE (users.db)")
    print("=" * 80)
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nTable Structure:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Get all users
    cursor.execute("SELECT id, full_name, email, mobile FROM users")
    users = cursor.fetchall()
    
    print(f"\nTotal Users: {len(users)}")
    print("\nUser Records:")
    print("-" * 80)
    for user in users:
        print(f"ID: {user[0]}")
        print(f"Name: {user[1]}")
        print(f"Email: {user[2]}")
        print(f"Mobile: {user[3]}")
        print("-" * 80)
    
    conn.close()

def view_vets_db():
    print("\n" + "=" * 80)
    print("VETS DATABASE (vets.db)")
    print("=" * 80)
    
    conn = sqlite3.connect('vets.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(vets)")
    columns = cursor.fetchall()
    print("\nTable Structure:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Get all vets
    cursor.execute("SELECT id, full_name, email, license_id, region FROM vets")
    vets = cursor.fetchall()
    
    print(f"\nTotal Vets: {len(vets)}")
    print("\nVet Records:")
    print("-" * 80)
    for vet in vets:
        print(f"ID: {vet[0]}")
        print(f"Name: {vet[1]}")
        print(f"Email: {vet[2]}")
        print(f"License: {vet[3]}")
        print(f"Region: {vet[4]}")
        print("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    try:
        view_users_db()
        view_vets_db()
        print("\n✓ Database viewing completed successfully!\n")
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
