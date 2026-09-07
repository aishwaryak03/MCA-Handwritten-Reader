# AI-Based Regional Language Handwritten Document Reader and Intelligent Information Extraction System

A complete MCA final-semester project implementation using Flask, EasyOCR, OpenCV, language detection, MongoDB/SQLite storage, and a browser-based frontend.

## Main features

- Upload JPG, JPEG, PNG and PDF documents
- PDF pages are converted to images automatically
- Image preprocessing: upscale, grayscale/contrast enhancement and optional deskew
- OCR for English, Hindi, Marathi and Kannada
- Automatic language/script detection
- OCR confidence reporting
- OCR-tolerant information extraction:
  - Name
  - Phone
  - Email
  - Date
  - Amount
  - PIN code
  - Address
  - Organization
- Document history
- JSON and CSV export
- Generated PDF extraction report
- Simple responsive web interface
- SQLite fallback for easy local execution
- MongoDB support when configured
- Automated backend tests

## Project structure

backend/
  app.py
  config.py
  database.py
  requirements.txt
  routes/
    process.py
  services/
    preprocess.py
    ocr.py
    language.py
    extractor.py
    export.py
  tests/
    test_extractor.py
  uploads/
  exports/

frontend/
  index.html
  style.css
  app.js

## Quick start on Windows PowerShell

```powershell
cd C:\MCA-Projects\MCA-Handwritten-Reader
python -m venv backend\venv
backend\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m spacy download en_core_web_sm
python backend\app.py
```

Then open:

http://127.0.0.1:5000

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

and activate again.

## EasyOCR model download

On first OCR execution, EasyOCR may download its model files. Internet access is required for that first model download.

## MongoDB

MongoDB is optional.

Without MongoDB, the project automatically uses SQLite at:

`backend/data/app.db`

To use MongoDB, create `backend/.env`:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=handwritten_reader
```

The application will use MongoDB when the connection succeeds; otherwise it uses SQLite.

## API

POST `/api/process`

Multipart field:
`file`

Optional form field:
`language`

Allowed language values:
`auto`, `en`, `hi`, `mr`, `kn`

GET `/api/documents`

GET `/api/documents/<id>`

GET `/api/health`

GET `/api/export/<id>/json`

GET `/api/export/<id>/csv`

GET `/api/export/<id>/pdf`

## Notes

Handwritten OCR accuracy depends heavily on handwriting quality, image resolution, lighting, skew and the language model. The extraction layer intentionally performs contextual normalization for common OCR errors instead of blindly replacing characters across the entire document.
