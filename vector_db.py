import os
import gc
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import DB_PATH, GEMINI_API_KEY
from load_data import load_pdf, split_text

# Ensure Google API key is set in environment for GoogleGenerativeAIEmbeddings
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Initialize Google GenAI text embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def initialize_vector_db():
    """
    Initialize or load the ChromaDB vector store.
    
    If the database directory exists but contains 0 documents (e.g., fresh deployment),
    it automatically loads and ingests PDFs in small batches to save memory.
    """
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH, exist_ok=True)

    # Initialize Chroma using Cosine similarity metric
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model,
        collection_metadata={"hnsw:space": "cosine"}
    )

    # Check if database is empty and run auto-ingestion if necessary
    try:
        doc_count = vector_db._collection.count()
    except Exception as e:
        print(f"⚠️ Could not read document count: {e}")
        doc_count = 0

    if doc_count == 0:
        print("⚡ Vector store is empty! Starting automatic ingestion...")
        try:
            raw_docs = load_pdf()
            chunks = split_text(raw_docs)

            # Ingest in small micro-batches to prevent Memory/OOM errors
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                vector_db.add_documents(batch)
                gc.collect()

            print(f"✅ Successfully ingested {len(chunks)} chunks into ChromaDB!")
        except Exception as e:
            print(f"❌ Auto-ingestion failed during startup: {e}")

    return vector_db


def store_embeddings(docs):
    """
    Store or append new document embeddings into ChromaDB without overwriting existing data.
    """
    vector_db = initialize_vector_db()
    vector_db.add_documents(docs)
    return vector_db


def retrieve_docs(query, vector_db):
    """
    Retrieve top-k relevant documents from ChromaDB.
    """
    if vector_db is None:
        print("⚠️ Vector database instance is None.")
        return []

    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    return retriever.invoke(query)
