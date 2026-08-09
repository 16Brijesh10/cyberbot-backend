import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import DB_PATH, GEMINI_API_KEY

# Initialize Google's official LangChain embedding wrapper
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
)


def initialize_vector_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)

    return Chroma(
        persist_directory=DB_PATH,
        embedding_function=embedding_model
    )


def store_embeddings(docs):
    return Chroma.from_documents(
        docs,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )


def retrieve_docs(query, vector_db):
    retriever = vector_db.as_retriever(search_kwargs={"k": 15})
    return retriever.invoke(query)
