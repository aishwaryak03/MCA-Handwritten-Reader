import csv
import io
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def json_bytes(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")


def csv_bytes(doc):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Field", "Value"])
    for key, value in doc.get("extracted", {}).items():
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        writer.writerow([key, value])
    return output.getvalue().encode("utf-8")


def pdf_bytes(doc):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(45, y, "Handwritten Document Extraction Report")
    y -= 30

    pdf.setFont("Helvetica", 10)
    pdf.drawString(45, y, f"File: {doc.get('filename', '')}")
    y -= 16
    pdf.drawString(45, y, f"Language: {doc.get('language', '')}")
    y -= 16
    pdf.drawString(45, y, f"OCR Confidence: {doc.get('confidence', 0):.2%}")
    y -= 28

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(45, y, "Extracted Information")
    y -= 22

    pdf.setFont("Helvetica", 10)
    for key, value in doc.get("extracted", {}).items():
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        value = str(value)
        if len(value) > 90:
            value = value[:87] + "..."
        pdf.drawString(50, y, f"{key.replace('_', ' ').title()}: {value}")
        y -= 17
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
