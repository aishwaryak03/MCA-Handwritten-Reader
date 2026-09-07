import uuid
from pathlib import Path

import fitz
from flask import Blueprint, jsonify, request, send_file

from config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB, UPLOAD_DIR
from database import db, now_iso
from services.extractor import extract_information
from services.language import detect_language
from services.ocr import perform_ocr
from services.preprocess import preprocess_image
from services.export import json_bytes, csv_bytes, pdf_bytes

process_bp = Blueprint("process", __name__, url_prefix="/api")


def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def pdf_to_images(pdf_path, work_dir):
    document = fitz.open(pdf_path)
    paths = []
    for index, page in enumerate(document):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        output = work_dir / f"page_{index + 1}.png"
        pix.save(str(output))
        paths.append(output)
    document.close()
    return paths


@process_bp.post("/process")
def process_document():
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No filename supplied."}), 400

    if not allowed(file.filename):
        return jsonify({"error": "Allowed formats: JPG, JPEG, PNG, PDF."}), 400

    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)

    if size > MAX_UPLOAD_MB * 1024 * 1024:
        return jsonify({"error": f"Maximum file size is {MAX_UPLOAD_MB} MB."}), 413

    doc_id = uuid.uuid4().hex
    safe_name = Path(file.filename).name
    suffix = Path(safe_name).suffix.lower()
    original_path = UPLOAD_DIR / f"{doc_id}{suffix}"
    file.save(original_path)

    work_dir = UPLOAD_DIR / doc_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        requested_language = request.form.get("language", "auto").lower()

        if suffix == ".pdf":
            image_paths = pdf_to_images(original_path, work_dir)
        else:
            image_paths = [original_path]

        page_results = []
        combined_text = []
        all_conf = []

        for image_path in image_paths:
            processed = preprocess_image(image_path)

            if requested_language in {"en", "hi", "mr", "kn"}:
                ocr_language = requested_language
            else:
                # English reader is used for the first pass in auto mode.
                # Script detection then determines whether a regional reader
                # should be run.
                ocr_language = "en"

            result = perform_ocr(processed, ocr_language)

            detected = detect_language(result["text"])

            # Re-run using the relevant regional model when auto detection
            # identifies one.
            if requested_language == "auto" and detected in {"hi", "mr", "kn"}:
                regional = perform_ocr(processed, detected)
                if regional["confidence"] >= result["confidence"] or detected == "kn":
                    result = regional

            page_results.append({
                "page": len(page_results) + 1,
                "text": result["text"],
                "confidence": result["confidence"],
                "detections": result["detections"],
            })
            combined_text.append(result["text"])
            all_conf.append(result["confidence"])

        final_text = "\n".join(t for t in combined_text if t.strip())
        final_language = (
            requested_language if requested_language != "auto"
            else detect_language(final_text)
        )

        confidence = sum(all_conf) / len(all_conf) if all_conf else 0.0
        extracted = extract_information(final_text, final_language)

        doc = {
            "id": doc_id,
            "filename": safe_name,
            "language": final_language,
            "confidence": round(confidence, 4),
            "ocr_text": final_text,
            "extracted": extracted,
            "pages": page_results,
            "created_at": now_iso(),
        }

        db.insert_document(doc)
        return jsonify(doc), 200

    except Exception as exc:
        return jsonify({
            "error": "Document processing failed.",
            "details": str(exc)
        }), 500


@process_bp.get("/documents")
def documents():
    return jsonify(db.list_documents())


@process_bp.get("/documents/<doc_id>")
def document(doc_id):
    result = db.get_document(doc_id)
    if not result:
        return jsonify({"error": "Document not found."}), 404
    return jsonify(result)


@process_bp.get("/export/<doc_id>/json")
def export_json(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    data = json_bytes(doc)
    from io import BytesIO
    return send_file(BytesIO(data), mimetype="application/json",
                     as_attachment=True, download_name=f"{doc_id}.json")


@process_bp.get("/export/<doc_id>/csv")
def export_csv(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    data = csv_bytes(doc)
    from io import BytesIO
    return send_file(BytesIO(data), mimetype="text/csv",
                     as_attachment=True, download_name=f"{doc_id}.csv")


@process_bp.get("/export/<doc_id>/pdf")
def export_pdf(doc_id):
    doc = db.get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found."}), 404
    data = pdf_bytes(doc)
    from io import BytesIO
    return send_file(BytesIO(data), mimetype="application/pdf",
                     as_attachment=True, download_name=f"{doc_id}.pdf")
