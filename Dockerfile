# Use an official Python runtime as a base image
FROM python:3.10-slim

# Install system dependencies (VERY IMPORTANT)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Upgrade pip (important for dependency resolver)
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
