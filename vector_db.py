import os
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from google import genai
from google.genai import types
from config import DB_PATH, GEMINI_API_KEY


class GeminiEmbeddings(Embeddings):
    def __init__(self):
        # Force v1beta REST API version
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={'api_version': 'v1beta'}
        )

    def embed_documents(self, texts):
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=texts
        )
        return [item.values for item in response.embeddings]

    def embed_query(self, text):
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values


embedding_model = GeminiEmbeddings()


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
