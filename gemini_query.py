
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
    Create a new SQLite connection.

    A new connection is created for each database operation
    instead of keeping a global connection/cursor.
    """

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


# ============================================================
# Initialize Database
# ============================================================

def initialize_chat_database():
    """
    Create the chat_history table if it does not exist.

    Chat history is intentionally cleared whenever the
    application starts to keep the deployment lightweight.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Create table if it doesn't already exist
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
        # This is intentional.
        # ----------------------------------------------------

        cursor.execute(
            "DELETE FROM chat_history"
        )

        conn.commit()

        print("🧹 Chat history cleared on startup.")

    except Exception as e:

        conn.rollback()

        print(
            "❌ Database initialization error:",
            repr(e)
        )

        raise

    finally:

        conn.close()


# Initialize database when application starts
initialize_chat_database()


# ============================================================
# Clean Email
# ============================================================

def clean_email(email):
    """
    Convert the email to a normal plain-text string.

    Handles values such as:

    brijesh.peju@gmail.com

    and accidentally formatted values such as:

    [brijesh.peju@gmail.com](mailto:brijesh.peju@gmail.com)
    """

    email = str(email).strip()

    # Handle Markdown email format
    if email.startswith("[") and "](" in email:

        try:

            email = email.split("](")[0]
            email = email.lstrip("[")

        except Exception:

            pass

    # Handle mailto: prefix
    if email.startswith("mailto:"):

        email = email.replace(
            "mailto:",
            "",
            1
        )

    return email.strip()


# ============================================================
# Save Chat To Database
# ============================================================

def save_to_db(
    email,
    user_query,
    assistant_response,
    chat_id
):
    """
    Save one user/assistant conversation to SQLite.

    The first message of a chat becomes the chat title.
    """

    # --------------------------------------------------------
    # Convert values to normal Python strings
    # --------------------------------------------------------

    email = clean_email(email)

    user_query = str(
        user_query
    )

    assistant_response = str(
        assistant_response
    )

    chat_id = str(
        chat_id
    )


    # --------------------------------------------------------
    # Create database connection
    # --------------------------------------------------------

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # Check whether this is the first message
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

        if count == 0:

            title = user_query

        else:

            title = None


        # Make sure title is SQLite-safe
        if title is not None:

            title = str(title)


        # ----------------------------------------------------
        # Insert conversation
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

        print("✅ Chat saved to SQLite.")


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
# Load Chat History By Chat ID
# ============================================================

def load_history_by_chat_id(
    email,
    chat_id
):
    """
    Load previous messages belonging to a specific chat.
    """

    email = clean_email(email)

    chat_id = str(
        chat_id
    )


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
# Load Chat History By Date
# ============================================================

def load_history_by_date(
    email,
    selected_date
):
    """
    Load chat history for a specific date.
    """

    email = clean_email(email)

    selected_date = str(
        selected_date
    )


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
# Extract Gemini Text
# ============================================================

def extract_gemini_text(response):
    """
    Extract only the actual text from a Gemini response.

    Newer versions of LangChain/Gemini may return:

    [
        {
            "type": "text",
            "text": "Hello!",
            "extras": {
                "signature": "..."
            }
        }
    ]

    We only want the 'text' field.

    The signature and other metadata are ignored.
    """

    # --------------------------------------------------------
    # Get response content
    # --------------------------------------------------------

    if not hasattr(
        response,
        "content"
    ):

        return str(
            response
        ).strip()


    content = response.content


    # --------------------------------------------------------
    # Content is a list
    # --------------------------------------------------------

    if isinstance(
        content,
        list
    ):

        text_parts = []


        for item in content:

            # -----------------------------------------------
            # Dictionary content block
            # -----------------------------------------------

            if isinstance(
                item,
                dict
            ):

                if item.get(
                    "type"
                ) == "text":

                    text = item.get(
                        "text",
                        ""
                    )

                    if text:

                        text_parts.append(
                            str(text)
                        )


            # -----------------------------------------------
            # Plain string content block
            # -----------------------------------------------

            elif isinstance(
                item,
                str
            ):

                text_parts.append(
                    item
                )


        return "".join(
            text_parts
        ).strip()


    # --------------------------------------------------------
    # Content is already a string
    # --------------------------------------------------------

    return str(
        content
    ).strip()


# ============================================================
# Query Gemini
# ============================================================

def query_gemini(
    query,
    retrieved_docs,
    email,
    chat_id
):
    """
    Query Gemini using:

    1. Retrieved company documents
    2. Previous conversation history
    3. Current user question
    """

    # --------------------------------------------------------
    # Normalize inputs
    # --------------------------------------------------------

    query = str(
        query
    )

    email = clean_email(
        email
    )

    chat_id = str(
        chat_id
    )


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

        context_parts = []

        for doc in retrieved_docs:

            if hasattr(
                doc,
                "page_content"
            ):

                content = str(
                    doc.page_content
                )

                if content.strip():

                    context_parts.append(
                        content
                    )


        if context_parts:

            context = "\n\n".join(
                context_parts
            )

        else:

            context = (
                "No relevant company information "
                "was retrieved."
            )

    else:

        context = (
            "No relevant company information "
            "was retrieved from the company "
            "knowledge base."
        )


    # --------------------------------------------------------
    # Build conversation history
    # --------------------------------------------------------

    if conversation_history:

        history_parts = []

        for q, a in conversation_history:

            history_parts.append(
                f"User: {str(q)}\n"
                f"Assistant: {str(a)}"
            )


        history = "\n\n".join(
            history_parts
        )

    else:

        history = (
            "No previous conversation."
        )


    # --------------------------------------------------------
    # Gemini Prompt
    # --------------------------------------------------------

    full_prompt = f"""
You are an AI assistant that answers questions about a company.

Use the provided company information and conversation history
to answer the user's question.

RULES:

1. Use the provided company information as the primary source
   for company-related questions.

2. Do not invent company policies, rules, procedures, benefits,
   or other company-specific information.

3. If the provided company information does not contain enough
   information to answer a company-related question, clearly
   state that the available company information does not
   provide the answer.

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

    print("🤖 Calling Gemini...")

    response = gemini_llm.invoke(
        full_prompt
    )


    # --------------------------------------------------------
    # Extract ONLY text
    # --------------------------------------------------------

    answer = extract_gemini_text(
        response
    )


    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if not answer:

        answer = (
            "Sorry, I could not generate a response."
        )


    # Make absolutely sure SQLite receives a string
    answer = str(
        answer
    )


    # --------------------------------------------------------
    # Save conversation
    # --------------------------------------------------------

    save_to_db(
        email=email,
        user_query=query,
        assistant_response=answer,
        chat_id=chat_id
    )


    # --------------------------------------------------------
    # Return clean answer to FastAPI
    # --------------------------------------------------------

    return answer

