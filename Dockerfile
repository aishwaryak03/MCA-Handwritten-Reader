FROM python:3.12-slim

# Install Tesseract OCR, regional language data,
# and Linux libraries required by OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-hin \
        tesseract-ocr-mar \
        tesseract-ocr-kan \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app

WORKDIR /app/backend

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300