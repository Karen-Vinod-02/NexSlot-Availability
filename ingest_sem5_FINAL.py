from pathlib import Path
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

print("🚀 INGESTING SEMESTER 5")

DATA_DIR = Path("data/sem5")
DB_DIR = "chroma_db_sem5"

emb = OllamaEmbeddings(model="qwen2.5:1.5b")

documents = []

for pdf in DATA_DIR.glob("*.pdf"):
    print("📄 Loading:", pdf.name)
    loader = PyPDFLoader(str(pdf))
    pages = loader.load()
    for p in pages:
        p.metadata["source"] = pdf.name  # 🔴 CRITICAL
        documents.append(p)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

chunks = splitter.split_documents(documents)
print("🧩 Chunks created:", len(chunks))

db = Chroma.from_documents(
    documents=chunks,
    embedding=emb,
    persist_directory=DB_DIR
)

print("✅ Stored vectors:", db._collection.count())

