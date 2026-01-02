#!/usr/bin/env python3
"""
Debug script to check ChromaDB state and diagnose issues
"""

import os
from pathlib import Path
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

print("🔍 CHROMA DEBUG SCRIPT")
print("=" * 50)

# Check directory structure
DB = "chroma_db_general"
print(f"📁 Checking directory: {DB}")

if os.path.exists(DB):
    print(f"✅ Directory exists")
    files = list(Path(DB).rglob("*"))
    print(f"📊 Files in DB: {len(files)}")
    for f in files[:5]:  # Show first 5 files
        print(f"   - {f.name}")
else:
    print(f"❌ Directory does not exist")

# Try to connect to existing DB
try:
    print(f"\n🔌 Attempting to connect to ChromaDB...")
    emb = OllamaEmbeddings(model="qwen2.5:1.5b")
    
    vectordb = Chroma(
        persist_directory=DB,
        embedding_function=emb
    )
    
    print(f"✅ Connected successfully")
    print(f"📦 Collection count: {vectordb._collection.count()}")
    
    # Get collection info
    collection = vectordb._collection
    print(f"🆔 Collection name: {collection.name}")
    
    # Try to get a sample document
    if collection.count() > 0:
        sample = collection.get(limit=1)
        print(f"📄 Sample document metadata: {sample['metadatas'][0] if sample['metadatas'] else 'None'}")
        print(f"📝 Sample document content: {sample['documents'][0][:100] if sample['documents'] else 'None'}...")
    else:
        print("❌ No documents found")
        
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test data file
data_file = "data/vesit_general.txt"
print(f"\n📄 Checking data file: {data_file}")
if os.path.exists(data_file):
    size = os.path.getsize(data_file)
    print(f"✅ File exists, size: {size} bytes")
else:
    print(f"❌ File does not exist")
