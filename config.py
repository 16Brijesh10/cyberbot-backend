import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PDF_PATHS = [
    os.path.join(BASE_DIR, "CyberTech Information Security Guidelines - Do's  Don'ts.pdf"),
    os.path.join(BASE_DIR, "CyberTech Reference Manual_CyberTech_Code of Business Conduct and Ethics_ V_04.3.pdf"),
    os.path.join(BASE_DIR, "CyberTech WorkFromHome Guidelines.pdf"),
    os.path.join(BASE_DIR, "Joining Documents Checklist.pdf")
]

DB_PATH = os.path.join(BASE_DIR, "db")
