
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

# === Internal Imports ===

from vector_db import retrieve_docs, initialize_vector_db
from gemini_query import query_gemini, load_history_by_chat_id


# ============================================================
# SQLite Database
# ============================================================

conn = sqlite3.connect(
    "chat_history.db",
    check_same_thread=False
)

cursor = conn.cursor()


# ============================================================
# FastAPI
# ============================================================

app = FastAPI()


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ChromaDB
# ============================================================
#
# IMPORTANT:
# Do NOT load PDFs or generate embeddings here.
#
# Render has only 512 MB RAM, so PDF processing during
# application startup can cause the process to be killed.
# ============================================================

print("🔄 Initializing ChromaDB...")

try:
    vector_db = initialize_vector_db()
    print("✅ ChromaDB initialized successfully.")

except Exception as e:
    print("❌ Failed to initialize ChromaDB:", e)
    vector_db = None


# ============================================================
# Pydantic Models
# ============================================================

class ChatRequest(BaseModel):
    message: str
    email: str
    chat_id: str


class HistoryRequest(BaseModel):
    email: str
    chat_id: str


# ============================================================
# Health Check
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "CyberTech RAG API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "vector_db": vector_db is not None
    }


# ============================================================
# Chat
# ============================================================

@app.post("/chat")
def chat(req: ChatRequest):

    print("✅ Received ChatRequest:", req)

    if vector_db is None:
        return {
            "answer": "Vector database is not available."
        }

    try:

        # ----------------------------------------------------
        # Step 1: Retrieve documents
        # ----------------------------------------------------

        print("🔍 Step 1: Retrieving documents from ChromaDB...")

        docs = retrieve_docs(
            req.message,
            vector_db
        )

        print(
            f"📚 Step 2: Retrieved {len(docs)} documents."
        )


        # ----------------------------------------------------
        # Step 2: Query Gemini
        # ----------------------------------------------------

        print("🤖 Step 3: Querying Gemini model...")

        response = query_gemini(
            req.message,
            docs,
            req.email,
            req.chat_id
        )

        print("✅ Step 4: Gemini response obtained.")

        return {
            "answer": response
        }

    except Exception as e:

        print(
            "❌ ERROR in /chat:",
            str(e)
        )

        return {
            "answer":
                "Sorry, something went wrong while processing your request."
        }


# ============================================================
# Chat History
# ============================================================

@app.post("/history")
def get_history(req: HistoryRequest):

    raw_history = load_history_by_chat_id(
        req.email,
        req.chat_id
    )

    formatted = []

    for q, a in raw_history:

        formatted.append({
            "role": "user",
            "content": q
        })

        formatted.append({
            "role": "assistant",
            "content": a
        })

    return {
        "messages": formatted,
        "chatId": req.chat_id
    }


# ============================================================
# Chat Titles
# ============================================================

@app.get("/history/titles")
def get_titles(email: str):

    cursor.execute(
        """
        SELECT DISTINCT
            chat_id,
            MIN(title),
            DATE(timestamp)
        FROM chat_history
        WHERE email = ?
          AND title IS NOT NULL
        GROUP BY chat_id
        ORDER BY MAX(timestamp) DESC
        """,
        (email,)
    )

    results = cursor.fetchall()

    return {
        "titles": [
            {
                "chatId": chat_id,
                "title": title or "Untitled",
                "date": date
            }
            for chat_id, title, date in results
        ]
    }
