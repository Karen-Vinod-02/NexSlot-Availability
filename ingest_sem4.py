#!/usr/bin/env python3
"""
Semester 4 Data Ingestion for VESIT Chatbot
Loads Semester 4 PDFs into chroma_db_sem4
"""

import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

print("📚 Starting VESIT Semester 4 data ingestion...")

# =========================
# ABSOLUTE PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "sem4"
CHROMA_DIR = BASE_DIR / "chroma_db_sem4"

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Data directory: {DATA_DIR}")
print(f"📁 Target ChromaDB: {CHROMA_DIR}")

documents = []

# =========================
# LOAD PDFs
# =========================
pdf_files = list(DATA_DIR.glob("*.pdf"))
print(f"📄 Found {len(pdf_files)} Semester 4 PDFs")

for pdf in pdf_files:
    print(f"📄 Loading PDF: {pdf.name}")
    loader = PyPDFLoader(str(pdf))
    docs = loader.load()
    for d in docs:
        d.metadata = {
            "source": pdf.name, 
            "type": "pdf",
            "semester": "4",
            "portal": "sem4"
        }
    documents.extend(docs)

# =========================
# SAFETY CHECK
# =========================
if not documents:
    raise RuntimeError("❌ No Semester 4 documents loaded. Check data/sem4 structure.")

print(f"📊 Total documents loaded: {len(documents)}")

# =========================
# SPLIT
# =========================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200
)

chunks = splitter.split_documents(documents)
print(f"🧩 Created {len(chunks)} chunks")

# =========================
# EMBEDDINGS + VECTOR DB
# =========================
embeddings = OllamaEmbeddings(
    model="qwen2.5:1.5b",
    base_url="http://localhost:11434"
)

if CHROMA_DIR.exists():
    shutil.rmtree(CHROMA_DIR)

Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=str(CHROMA_DIR)
)

print("✅ SEMESTER 4 INGESTION COMPLETE")
print(f"📁 Vector DB created at: {CHROMA_DIR}")
