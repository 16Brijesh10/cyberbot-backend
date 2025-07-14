import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_PATH = [
    os.path.join(BASE_DIR, "CyberTech Information Security Guidelines - Do's  Don'ts.pdf"),
    os.path.join(BASE_DIR, "CyberTech Reference Manual_CyberTech_Code of Business Conduct and Ethics_ V_04.3.pdf"),
    os.path.join(BASE_DIR, "CyberTech WorkFromHome Guidelines.pdf"),
]

# Use /tmp for writable db directory on Render
DB_PATH = "/tmp/db"
