# System Testing – AI-Based Regional Language Handwritten Document Reader

## 1. Functional Test Cases

| Test ID | Module | Test Description | Expected Result | Status |
|---|---|---|---|---|
| TC01 | File Upload | Upload a valid handwritten PNG/JPG image | Image is accepted and processed | PASS |
| TC02 | OCR | Process English handwritten document | OCR text is generated | PASS |
| TC03 | OCR | Process Hindi handwritten document | OCR text is generated | PASS |
| TC04 | OCR | Process Marathi handwritten document | OCR text is generated | PASS |
| TC05 | OCR | Process Kannada handwritten document | OCR text is generated | PASS |
| TC06 | Language Detection | Detect language from OCR text | Detected language is displayed | PASS |
| TC07 | Information Extraction | Extract name from document | Name is displayed when recognized | PASS |
| TC08 | Information Extraction | Extract phone number | Phone number is displayed when recognized | PASS |
| TC09 | Information Extraction | Extract email address | Email is displayed when recognized | PASS |
| TC10 | Information Extraction | Extract date | Date is displayed when recognized | PASS |
| TC11 | Information Extraction | Extract amount | Amount is displayed when recognized | PASS |
| TC12 | Information Extraction | Extract PIN code | PIN code is displayed when recognized | PASS |
| TC13 | Database | Store processed document result | Record is stored in SQLite database | PASS |
| TC14 | JSON Export | Export extracted information as JSON | JSON file is generated | PASS |
| TC15 | CSV Export | Export extracted information as CSV | CSV file is generated | PASS |
| TC16 | PDF Export | Export extracted information as PDF | PDF file is generated | PASS |
| TC17 | UI | Display OCR result and extracted fields | Results are clearly displayed | PASS |
| TC18 | Error Handling | Upload/process invalid input | Application handles the error without crashing | PASS |

## 2. Automated Unit Tests

The project includes automated tests for the information extraction module.

Executed using:

    python -m pytest -v

Current automated tests cover:
- Clean information extraction
- Split amount extraction
- OCR-tolerant email extraction

## 3. Test Evidence

Screenshots are stored under:

    docs/screenshots/testing/

The export evidence is stored under:

    docs/screenshots/exports/

UI screenshots are stored under:

    docs/screenshots/ui/

## 4. Export Evidence

The system successfully generated:
- JSON export
- CSV export
- PDF export

## 5. Database Evidence

The SQLite database contains processed document records.

Database location:

    backend/data/app.db
