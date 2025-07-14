from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from vector_db import retrieve_docs, initialize_vector_db
from gemini_query import query_gemini, load_history_by_chat_id
import sqlite3

# DB connection
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector DB
vector_db = initialize_vector_db()

# Schemas
class ChatRequest(BaseModel):
    message: str
    email: str
    chat_id: str

class HistoryRequest(BaseModel):
    email: str
    chat_id: str

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
