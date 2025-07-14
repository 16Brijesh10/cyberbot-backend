from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

# === Internal Imports ===
from vector_db import retrieve_docs, initialize_vector_db, store_embeddings
from gemini_query import query_gemini, load_history_by_chat_id
from load_data import load_pdf, split_text
from config import DB_PATH

# === DB Connection ===
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# === Initialize FastAPI ===
app = FastAPI()

# === Enable CORS (For Frontend Access) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Vector DB Initialization ===
vector_db = initialize_vector_db()

# === Load & Embed PDFs on First Run ===
vector_db_index = os.path.join(DB_PATH, "index")
if not os.path.exists(vector_db_index) or not os.listdir(DB_PATH):
    print("📄 No vector DB found. Loading and embedding PDFs...")
    try:
        docs = load_pdf()
        chunks = split_text(docs)
        store_embeddings(chunks)
        print("✅ PDF embeddings stored in ChromaDB.")
    except Exception as e:
        print("❌ Failed to embed PDFs:", e)
else:
    print("📁 Existing vector DB found. Skipping embedding.")


# === Pydantic Models ===
class ChatRequest(BaseModel):
    message: str
    email: str
    chat_id: str

class HistoryRequest(BaseModel):
    email: str
    chat_id: str


# === Routes ===
@app.post("/chat")
def chat(req: ChatRequest):
    print("✅ Received ChatRequest:", req)

    try:
        print("🔍 Step 1: Retrieving documents from ChromaDB...")
        docs = retrieve_docs(req.message, vector_db)
        print(f"📚 Step 2: Retrieved {len(docs)} documents.")

        print("🤖 Step 3: Querying Gemini model...")
        response = query_gemini(req.message, docs, req.email, req.chat_id)
        print("✅ Step 4: Gemini response obtained.")

        return {"answer": response}
    except Exception as e:
        print("❌ ERROR in /chat:", str(e))
        return {"answer": "Sorry, something went wrong while processing your request."}


@app.post("/history")
def get_history(req: HistoryRequest):
    raw_history = load_history_by_chat_id(req.email, req.chat_id)
    
    formatted = []
    for q, a in raw_history:
        formatted.append({"role": "user", "content": q})
        formatted.append({"role": "assistant", "content": a})
    
    return {
        "messages": formatted,
        "chatId": req.chat_id
    }


@app.get("/history/titles")
def get_titles(email: str):
    cursor.execute("""
        SELECT DISTINCT chat_id, MIN(title), DATE(timestamp)
        FROM chat_history
        WHERE email = ? AND title IS NOT NULL
        GROUP BY chat_id
        ORDER BY MAX(timestamp) DESC
    """, (email,))
    
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
