# config.py
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PDF_PATH = PDF_PATHS = ["CyberTech Information Security Guidelines - Do's  Don'ts.pdf",
                        "CyberTech Reference Manual_CyberTech_Code of Business Conduct and Ethics_ V_04.3.pdf",
                        "CyberTech WorkFromHome Guidelines.pdf",
                        "Joining Documents Checklist.pdf"]  # List of PDFs  # Preloaded PDF file
DB_PATH = "./db"  # Directory to store ChromaDB
#COMPANY_WEBSITE="If need enter the company websitte"