FROM python:3.12-slim

# Install Tesseract OCR and required language data
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-hin \
        tesseract-ocr-mar \
        tesseract-ocr-kan && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy project
COPY . /app

# Move into backend
WORKDIR /app/backend

# Start Flask application with Gunicorn
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300