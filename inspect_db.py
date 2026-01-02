#!/usr/bin/env python3
"""
Direct database inspection to bypass API issues
"""

import sqlite3
import os

DB_PATH = "chroma_db_general/chroma.sqlite3"

print("🔍 DIRECT DATABASE INSPECTION")
print("=" * 50)

if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables found: {[table[0] for table in tables]}")
        
        # Try to find collections/embeddings
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Records: {count}")
            
            if count > 0 and table_name in ['embeddings', 'documents', 'collections']:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample = cursor.fetchall()
                print(f"   Sample data: {len(sample)} records")
                for i, row in enumerate(sample):
                    print(f"     Row {i+1}: {str(row)[:100]}...")
        
        conn.close()
        print(f"\n✅ Database inspection complete")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
else:
    print(f"❌ Database file not found: {DB_PATH}")

# Also check if the directory exists
if os.path.exists("chroma_db_general"):
    files = list(os.listdir("chroma_db_general"))
    print(f"\n📁 Directory contents: {files}")
else:
    print(f"\n❌ Directory not found: chroma_db_general")
