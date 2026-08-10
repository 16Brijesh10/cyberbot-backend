import os
import sqlite3
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import DB_PATH, GEMINI_API_KEY
from load_data import load_pdf, split_text

# Set API Key for Google Embeddings
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Recommended Google GenAI embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")


def initialize_vector_db():
    """
    Initialize or load ChromaDB.
    
    If the database exists but contains 0 documents (e.g., on container cold-start 
    or fresh Render deployment), it automatically runs the loader and embeds your 
    PDFs into the store directly.
    """
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH, exist_ok=True)

    # Initialize ChromaDB with Cosine distance metric for optimal Gemini embeddings
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model,
        collection_metadata={"hnsw:space": "cosine"}
    )

    # Automatically check if vector store is empty
    try:
        doc_count = vector_db._collection.count()
    except Exception as e:
        print(f"⚠️ Could not check collection count: {e}")
        doc_count = 0

    if doc_count == 0:
        print("⚡ ChromaDB is empty! Running auto-ingestion on startup...")
        try:
            raw_docs = load_pdf()
            print(f"📄 Loaded {len(raw_docs)} document pages.")
            
            chunks = split_text(raw_docs)
            print(f"✂️ Created {len(chunks)} text chunks.")

            # Append documents to existing Chroma collection
            vector_db.add_documents(chunks)
            print("✅ Embeddings stored in ChromaDB successfully!")
            
        except Exception as e:
            print(f"❌ Ingestion failed during database initialization: {e}")

    return vector_db


def store_embeddings(docs):
    """
    Store or append new document embeddings into ChromaDB without overwriting.
    """
    vector_db = initialize_vector_db()
    vector_db.add_documents(docs)
    return vector_db


def retrieve_docs(query, vector_db):
    """
    Retrieve top-k relevant documents from ChromaDB based on user query.
    """
    if vector_db is None:
        print("⚠️ Vector database instance is None.")
        return []

    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    return retriever.invoke(query)
