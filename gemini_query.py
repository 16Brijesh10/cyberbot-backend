import os
import sqlite3
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY

# Set up API key
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Initialize Gemini Model (Updated model identifier)
gemini_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)

# Connect to SQLite database
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# Create table if it doesn't exist (Removed DROP TABLE to preserve chat history)
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    email TEXT,
    title TEXT,
    user_query TEXT,
    assistant_response TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


def parse_response_content(content) -> str:
    """Safely converts LLM response content to a plain string for SQLite."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            else:
                text_parts.append(str(part))
        return "\n".join(text_parts)
    return str(content)


def save_to_db(email, user_query, assistant_response, chat_id):
    cursor.execute("""
        SELECT COUNT(*) FROM chat_history WHERE email = ? AND chat_id = ?
    """, (email, chat_id))
    count = cursor.fetchone()[0]

    # Save user_query as title only for the first message in this chat session
    title = user_query if count == 0 else None

    # Guarantee string type before inserting into SQLite
    clean_response = parse_response_content(assistant_response)

    cursor.execute("""
        INSERT INTO chat_history (email, chat_id, title, user_query, assistant_response, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (email, chat_id, title, user_query, clean_response, datetime.now()))
    conn.commit()


def load_history_by_chat_id(email, chat_id):
    cursor.execute(
        "SELECT user_query, assistant_response FROM chat_history WHERE email = ? AND chat_id = ?",
        (email, chat_id)
    )
    return cursor.fetchall()


def query_gemini(query, retrieved_docs, email, chat_id):
    """Query Gemini while remembering previous messages."""
    conversation_history = load_history_by_chat_id(email, chat_id)

    context = "\n".join([doc.page_content for doc in retrieved_docs])
    history = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in conversation_history])

    full_prompt = f"""
You are an AI assistant that answers based on company data.
Use the following company data and conversation history to answer.
Answer must be precise and good no extra information

Company Data:
{context}

Conversation History:
{history}

User: {query}
Assistant:
    """

    response = gemini_llm.invoke(full_prompt)
    
    # Extract and parse content
    raw_content = getattr(response, "content", "No response received.")
    answer = parse_response_content(raw_content)

    save_to_db(email, query, answer, chat_id)

    return answer
