#gemini_query.py
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY

import os

# Set up API key
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Initialize Gemini Model
gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

import sqlite3
from datetime import datetime   

# Connect to SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect("chat_history.db",check_same_thread=False)
cursor = conn.cursor()

# Drop existing table (CAUTION: This will erase existing data)
#cursor.execute("DROP TABLE IF EXISTS chat_history")

# Create table again
cursor.execute("""
CREATE TABLE chat_history (
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


def save_to_db(email, user_query, assistant_response, chat_id):
    cursor.execute("""
        SELECT COUNT(*) FROM chat_history WHERE email = ? AND chat_id = ?
    """, (email, chat_id))
    count = cursor.fetchone()[0]

    # Save the user_query as title only if this is the first message in this chat_id
    title = user_query if count == 0 else None

    cursor.execute("""
        INSERT INTO chat_history (email, chat_id, title, user_query, assistant_response, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (email, chat_id, title, user_query, assistant_response, datetime.now()))
    conn.commit()



#def load_history_by_date(email, selected_date):
    #"""Load chat history for a specific date."""
    #cursor.execute(
     #   "SELECT user_query, assistant_response FROM chat_history WHERE email = ? AND strftime('%Y-%m-%d', timestamp)  = ?",
     #   (email, selected_date),
    #)
    #return cursor.fetchall()
def load_history_by_chat_id(email, chat_id):
    cursor.execute(
        "SELECT user_query, assistant_response FROM chat_history WHERE email = ? AND chat_id = ?",
        (email, chat_id)
    )
    return cursor.fetchall()




def query_gemini(query, retrieved_docs, email, chat_id):
    """Query Gemini while remembering previous messages."""
    conversation_history = load_history_by_chat_id(email, chat_id)

    
    #global conversation_history

    context = "\n".join([doc.page_content for doc in retrieved_docs])
    history = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in conversation_history])

    full_prompt = f"""
You are an AI assistant that answers based on company data.
Use the following company data and conversation history to answer.

Do not mention or reveal any PDF filenames, document titles, or source names in your response.


Company Data:
{context}

Conversation History:
{history}

User: {query}
Assistant:
    """

    response = gemini_llm.invoke(full_prompt)
    answer = response.content if hasattr(response, "content") else "No response received."

    conversation_history.append((query, answer))
    save_to_db(email, query, answer, chat_id)

    return answer
