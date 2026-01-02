#!/usr/bin/env python3
"""
IMPROVED General Data Ingestion with better text preprocessing
This helps the model understand abbreviations and variations
"""

import shutil
import re
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

print("🚀 Starting IMPROVED General Ingestion")

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "vesit_general.txt"
CHROMA_DIR = BASE_DIR / "chroma_db_general"

# =========================
# TEXT PREPROCESSING
# =========================
def preprocess_text(text):
    """
    Add context and expand abbreviations in the raw text
    This helps with retrieval accuracy
    """
    
    # Add explicit mappings at the beginning of chunks
    context_additions = """
VESIT stands for Vivekanand Education Society's Institute of Technology.
VESIT is the same as Vivekanand Education Society's Institute of Technology.
VESIT is located in Mumbai, India.
VES stands for Vivekanand Education Society.
    """.strip()
    
    # Ensure VESIT appears with its full name frequently
    text = re.sub(
        r'\bVESIT\b',
        'VESIT (Vivekanand Education Society\'s Institute of Technology)',
        text,
        count=5  # Only first 5 occurrences to avoid over-redundancy
    )
    
    # Add context at the beginning
    processed_text = context_additions + "\n\n" + text
    
    return processed_text

# =========================
# SAFETY CHECK
# =========================
if not DATA_FILE.exists():
    raise RuntimeError(f"❌ Data file not found: {DATA_FILE}")

print(f"📊 Data file size: {DATA_FILE.stat().st_size} bytes")

# =========================
# RESET DB
# =========================
if CHROMA_DIR.exists():
    shutil.rmtree(CHROMA_DIR)
    print("🗑️  Cleared existing ChromaDB")

# =========================
# LOAD & PREPROCESS
# =========================
print("📄 Loading website text")
loader = TextLoader(str(DATA_FILE), encoding="utf-8")
docs = loader.load()

print(f"📚 Documents loaded: {len(docs)}")

# Preprocess the text
for doc in docs:
    doc.page_content = preprocess_text(doc.page_content)

print("✨ Text preprocessing complete")

# =========================
# SPLIT WITH BETTER SETTINGS
# =========================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,        # Slightly smaller for more focused chunks
    chunk_overlap=100,     # Good overlap for context
    separators=["\n\n", "\n", ". ", " ", ""],  # Better splitting
    length_function=len,
)

chunks = splitter.split_documents(docs)
print(f"🧩 Chunks created: {len(chunks)}")

# =========================
# ADD METADATA
# =========================
for i, chunk in enumerate(chunks):
    chunk.metadata["chunk_id"] = i
    chunk.metadata["source"] = "Official VESIT Website"
    # Add searchable keywords to metadata
    if "VESIT" in chunk.page_content or "Vivekanand" in chunk.page_content:
        chunk.metadata["contains_vesit"] = True

print("📝 Metadata added to chunks")

# =========================
# EMBEDDINGS + VECTOR DB
# =========================
embeddings = OllamaEmbeddings(
    model="qwen2.5:1.5b",
    base_url="http://localhost:11434"
)

print("🔄 Creating ChromaDB with improved documents...")
Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=str(CHROMA_DIR)
)

print("✅ IMPROVED GENERAL DB INGESTION COMPLETE")
print(f"📁 Vector DB created at: {CHROMA_DIR}")
print(f"📦 Total chunks processed: {len(chunks)}")

# =========================
# VERIFICATION
# =========================
print("\n🔍 VERIFICATION:")
try:
    vectordb = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings
    )
    
    count = vectordb._collection.count()
    print(f"📦 Collection count: {count}")
    
    if count > 0:
        print("✅ SUCCESS: Documents successfully persisted!")
        
        # Test retrieval with VESIT query
        print("\n🧪 Testing retrieval with 'VESIT location':")
        results = vectordb.similarity_search("VESIT location", k=2)
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Content preview: {result.page_content[:150]}...")
            print(f"Metadata: {result.metadata}")
        
        print(f"\n🎯 GENERAL DB NOW HAS {count} DOCUMENTS!")
    else:
        print("❌ FAILED: No documents found in collection")
        
except Exception as e:
    print(f"❌ Verification error: {e}")

print("\n" + "="*60)
print("💡 TIPS FOR BETTER ACCURACY:")
print("="*60)
print("1. Run this script to re-ingest with improved preprocessing")
print("2. Make sure your vesit_general.txt mentions 'VESIT' and full name")
print("3. Restart your Flask app after re-ingestion")
print("4. Test with: 'Where is VESIT located?'")
print("="*60)