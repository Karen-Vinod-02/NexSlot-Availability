#!/usr/bin/env python3
"""
Clean ingestion script for VESIT Academic Assistant
Location-safe (works from any directory)
"""

import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

print("📚 Starting VESIT data ingestion...")

# =========================
# ABSOLUTE PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "college"
WEBSITE_DIR = DATA_DIR / "website"
CHROMA_DIR = BASE_DIR / "chroma_db"

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Data directory: {DATA_DIR}")
print(f"📁 Website directory: {WEBSITE_DIR}")

documents = []

# =========================
# LOAD PDFs
# =========================
pdf_files = list(DATA_DIR.glob("*.pdf"))
print(f"📄 Found {len(pdf_files)} PDFs")

for pdf in pdf_files:
    print(f"📄 Loading PDF: {pdf.name}")
    loader = PyPDFLoader(str(pdf))
    docs = loader.load()
    for d in docs:
        d.metadata = {"source": pdf.name, "type": "pdf"}
    documents.extend(docs)

# =========================
# LOAD WEBSITE TEXT
# =========================
txt_files = list(WEBSITE_DIR.glob("*.txt"))
print(f"🌐 Found {len(txt_files)} website files")

for txt in txt_files:
    print(f"📝 Loading website file: {txt.name}")
    loader = TextLoader(str(txt), encoding="utf-8")
    docs = loader.load()
    for d in docs:
        d.metadata = {
            "source": "VESIT Official Website",
            "file": txt.name,
            "type": "website"
        }
    documents.extend(docs)

# =========================
# SAFETY CHECK
# =========================
if not documents:
    raise RuntimeError("❌ No documents loaded. Check data/college structure.")

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

print("✅ INGESTION COMPLETE")
print(f"📁 Vector DB created at: {CHROMA_DIR}")
