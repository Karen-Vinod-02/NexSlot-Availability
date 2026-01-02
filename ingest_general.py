import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

print("🚀 Starting GENERAL ingestion")

DB = "chroma_db_general"
DATA_FILE = "data/vesit_general.txt"

# Safety check
with open(DATA_FILE, "r", encoding="utf-8") as f:
    pass

# Reset DB
shutil.rmtree(DB, ignore_errors=True)

print("📄 Loading website text")
loader = TextLoader(DATA_FILE, encoding="utf-8")
docs = loader.load()

print("📚 Documents loaded:", len(docs))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

chunks = splitter.split_documents(docs)
print("🧩 Chunks created:", len(chunks))

emb = OllamaEmbeddings(model="qwen2.5:1.5b")

# ✅ CRITICAL FIX: keep handle + persist
vectordb = Chroma(
    persist_directory=DB,
    embedding_function=emb
)

vectordb.add_documents(chunks)
vectordb.persist()

print("✅ General DB ingestion COMPLETE")
print("📦 Persisted chunks:", vectordb._collection.count())
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

print("🚀 Starting GENERAL ingestion")

DB = "chroma_db_general"
DATA_FILE = "data/vesit_general.txt"

# Safety check
with open(DATA_FILE, "r", encoding="utf-8") as f:
    pass

# Reset DB
shutil.rmtree(DB, ignore_errors=True)

print("📄 Loading website text")
loader = TextLoader(DATA_FILE, encoding="utf-8")
docs = loader.load()

print("📚 Documents loaded:", len(docs))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

chunks = splitter.split_documents(docs)
print("🧩 Chunks created:", len(chunks))

emb = OllamaEmbeddings(model="qwen2.5:1.5b")

# ✅ CRITICAL FIX: keep handle + persist
vectordb = Chroma(
    persist_directory=DB,
    embedding_function=emb
)

vectordb.add_documents(chunks)
vectordb.persist()

print("✅ General DB ingestion COMPLETE")
print("📦 Persisted chunks:", vectordb._collection.count())
