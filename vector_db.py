#vector_db.py
import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import DB_PATH, GEMINI_API_KEY


# Set up Gemini API Key
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-002")

def initialize_vector_db():
    """Initialize or load the ChromaDB vector store."""
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)  # Create DB directory if not exists
    return Chroma(persist_directory=DB_PATH, embedding_function=embedding_model)

def store_embeddings(docs):
    """Store document embeddings in ChromaDB."""
    vector_db = Chroma.from_documents(docs, embedding=embedding_model, persist_directory=DB_PATH)
    return vector_db

def retrieve_docs(query, vector_db):
    """Retrieve relevant documents from ChromaDB."""
    retriever = vector_db.as_retriever(search_kwargs={"k": 15})
    return retriever.invoke(query)

