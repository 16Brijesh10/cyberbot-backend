
# gemini_query.py

import os
import sqlite3
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY


# ============================================================
# Gemini Configuration
# ============================================================

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2
)


# ============================================================
# SQLite Configuration
# ============================================================

DB_FILE = "chat_history.db"


def get_connection():
    """
    Create a lightweight SQLite connection.
    """

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


# ============================================================
# Initialize Chat Database
# ============================================================

def initialize_chat_database():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Create table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                email TEXT,
                title TEXT,
                user_query TEXT,
                assistant_response TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # Clear chat history on application restart
        #
        # This is intentional for your deployment.
        # ----------------------------------------------------

        cursor.execute(
            "DELETE FROM chat_history"
        )

        conn.commit()

        print("🧹 Chat history cleared on startup.")

    finally:

        conn.close()


# Initialize database
initialize_chat_database()


# ============================================================
# Clean Email
# ============================================================

def clean_email(email):
    """
    Convert the email into a plain string.

    Handles frontend values such as:

    [user@gmail.com](mailto:user@gmail.com)
    """

    email = str(email).strip()

    if email.startswith("[") and "](" in email:

        try:
            email = email.split("](")[0]
            email = email.lstrip("[")

        except Exception:
            pass

    if email.startswith("mailto:"):

        email = email.replace(
            "mailto:",
            "",
            1
        )

    return email.strip()


# ============================================================
# Save Chat
# ============================================================

def save_to_db(
    email,
    user_query,
    assistant_response,
    chat_id
):

    # --------------------------------------------------------
    # Convert everything to normal Python strings
    # --------------------------------------------------------

    email = clean_email(email)
    user_query = str(user_query)
    assistant_response = str(assistant_response)
    chat_id = str(chat_id)


    # --------------------------------------------------------
    # Create connection
    # --------------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # Check if this is the first message
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM chat_history
            WHERE email = ?
              AND chat_id = ?
            """,
            (
                email,
                chat_id
            )
        )

        count = cursor.fetchone()[0]


        # ----------------------------------------------------
        # First message becomes chat title
        # ----------------------------------------------------

        title = user_query if count == 0 else None


        # ----------------------------------------------------
        # Insert chat
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO chat_history (
                email,
                chat_id,
                title,
                user_query,
                assistant_response,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                chat_id,
                title,
                user_query,
                assistant_response,
                datetime.now().isoformat()
            )
        )

        conn.commit()

        print("✅ Chat saved.")

    except Exception as e:

        conn.rollback()

        print(
            "❌ SQLite save error:",
            repr(e)
        )

        raise

    finally:

        conn.close()


# ============================================================
# Load Chat History
# ============================================================

def load_history_by_chat_id(
    email,
    chat_id
):

    email = clean_email(email)
    chat_id = str(chat_id)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                user_query,
                assistant_response
            FROM chat_history
            WHERE email = ?
              AND chat_id = ?
            ORDER BY id ASC
            """,
            (
                email,
                chat_id
            )
        )

        return cursor.fetchall()

    finally:

        conn.close()


# ============================================================
# Load History By Date
# ============================================================

def load_history_by_date(
    email,
    selected_date
):

    email = clean_email(email)
    selected_date = str(selected_date)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                user_query,
                assistant_response
            FROM chat_history
            WHERE email = ?
              AND strftime('%Y-%m-%d', timestamp) = ?
            ORDER BY id ASC
            """,
            (
                email,
                selected_date
            )
        )

        return cursor.fetchall()

    finally:

        conn.close()


# ============================================================
# Query Gemini
# ============================================================

def query_gemini(
    query,
    retrieved_docs,
    email,
    chat_id
):

    # --------------------------------------------------------
    # Normalize input
    # --------------------------------------------------------

    query = str(query)
    email = clean_email(email)
    chat_id = str(chat_id)


    # --------------------------------------------------------
    # Load previous conversation
    # --------------------------------------------------------

    conversation_history = load_history_by_chat_id(
        email,
        chat_id
    )


    # --------------------------------------------------------
    # Build company context
    # --------------------------------------------------------

    if retrieved_docs:

        context = "\n\n".join(
            [
                str(doc.page_content)
                for doc in retrieved_docs
                if doc.page_content
            ]
        )

    else:

        context = (
            "No relevant company information was retrieved "
            "from the company knowledge base."
        )


    # --------------------------------------------------------
    # Build conversation history
    # --------------------------------------------------------

    if conversation_history:

        history = "\n\n".join(
            [
                f"User: {str(q)}\nAssistant: {str(a)}"
                for q, a in conversation_history
            ]
        )

    else:

        history = "No previous conversation."


    # --------------------------------------------------------
    # Gemini Prompt
    # --------------------------------------------------------

    full_prompt = f"""
You are an AI assistant that answers questions about a company.

Use the provided company information and conversation
history to answer the user's question.

RULES:

1. Use the provided company information as the primary
   source for company-related questions.

2. Do not invent company policies, rules, procedures,
   benefits, or other company-specific information.

3. If the provided company information does not contain
   enough information to answer a company-related question,
   clearly state that the available company information
   does not provide the answer.

4. You may answer simple greetings and normal conversation
   naturally.

5. Do not mention or reveal PDF filenames.

6. Do not mention internal document titles or source names.

7. Do not reveal internal retrieval information.

8. Use previous conversation history when relevant.

9. Keep responses clear and concise.

Company Information:
{context}

Previous Conversation:
{history}

User:
{query}

Assistant:
"""


    # --------------------------------------------------------
    # Call Gemini
    # --------------------------------------------------------

    response = gemini_llm.invoke(
        full_prompt
    )


    # --------------------------------------------------------
    # Extract response
    # --------------------------------------------------------

    if hasattr(response, "content"):

        answer = response.content

    else:

        answer = str(response)


    # --------------------------------------------------------
    # Make sure SQLite receives a string
    # --------------------------------------------------------

    answer = str(answer)


    # --------------------------------------------------------
    # Save conversation
    # --------------------------------------------------------

    save_to_db(
        email=email,
        user_query=query,
        assistant_response=answer,
        chat_id=chat_id
    )


    return answer

