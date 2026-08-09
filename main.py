#main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from vector_db import retrieve_docs, initialize_vector_db
from gemini_query import query_gemini, load_history_by_date

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with React domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db = initialize_vector_db()

class ChatRequest(BaseModel):
    message: str
    email: str

class DateRequest(BaseModel):
    date: str  # format: YYYY-MM-DD
    email: str

@app.post("/chat")
def chat(req: ChatRequest):
    docs = retrieve_docs(req.message, vector_db)
    response = query_gemini(req.message, docs, req.email)
    return {"answer": response}

@app.post("/history")
def get_history(req: DateRequest):
    raw_history = load_history_by_date(req.email, req.date)
    
    # Format into list of {role, content}
    formatted = []
    for q, a in raw_history:
        formatted.append({"role": "user", "content": q})
        formatted.append({"role": "assistant", "content": a})
    
    return {"history": formatted}
