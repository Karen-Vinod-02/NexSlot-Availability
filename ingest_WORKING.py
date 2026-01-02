from chromadb import Client
from chromadb.config import Settings
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

print("🚀 STARTING CLEAN INGEST")

# ---------- CONFIG ----------
DATA_DIR = Path("data/college/website")
DB_DIR = "chroma_db_general"
COLLECTION_NAME = "vesit_general"

# ---------- LOAD TEXT ----------
texts = []
for f in DATA_DIR.glob("*.txt"):
    content = f.read_text(encoding="utf-8", errors="ignore")
    if content.strip():
        texts.append(content)

print(f"📄 Loaded files: {len(texts)}")

if not texts:
    raise RuntimeError("NO TEXT FILES FOUND")

# ---------- SPLIT ----------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

docs = []
for t in texts:
    docs.extend(splitter.split_text(t))

print(f"🧩 Chunks created: {len(docs)}")

# ---------- EMBEDDINGS ----------
emb = OllamaEmbeddings(model="qwen2.5:1.5b")

# ---------- CHROMA ----------
client = Client(
    Settings(
        persist_directory=DB_DIR,
        anonymized_telemetry=False
    )
)

# ❗ EXPLICIT COLLECTION CREATION
collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

# ---------- ADD DATA ----------
# ---------- MANUAL EMBEDDING ----------
print("🧠 Generating embeddings...")
vectors = emb.embed_documents(docs)

print("💾 Storing in Chroma...")
collection.add(
    documents=docs,
    embeddings=vectors,
    ids=[f"id_{i}" for i in range(len(docs))]
)



print("✅ INGEST COMPLETE")
print("📦 Stored vectors:", collection.count())

