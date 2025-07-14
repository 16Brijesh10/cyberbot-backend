from web_scraper import scrape_company_website
from config import COMPANY_WEBSITE
from langchain.schema import Document

web_texts = scrape_company_website(COMPANY_WEBSITE)
website_documents = [Document(page_content=text, metadata={"source": "website"}) for text in web_texts]
print(len(website_documents))
print(website_documents)

import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import DB_PATH, GEMINI_API_KEY
import shutil

# Set up Gemini API Key
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vector_db = Chroma.from_documents(website_documents, embedding=embedding_model, persist_directory=DB_PATH)
print(vector_db)
