#!/usr/bin/env python3
"""
Quick check of sem4 database to verify working scripts
"""

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

print("🔍 CHECKING SEM4 DATABASE")

try:
    embeddings = OllamaEmbeddings(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434"
    )
    
    vectordb = Chroma(
        persist_directory="chroma_db_sem4",
        embedding_function=embeddings
    )
    
    count = vectordb._collection.count()
    print(f"📦 Sem4 collection count: {count}")
    
    if count > 0:
        sample = vectordb._collection.get(limit=1)
        print(f"📝 Sample content: {sample['documents'][0][:100]}...")
    else:
        print("❌ Sem4 also has 0 documents!")
        
except Exception as e:
    print(f"❌ Error: {e}")
