import os
import shutil

import cv2
import numpy as np
import pytesseract


LANGUAGE_MODELS = {
    "en": "eng",
    "hi": "eng+hin",
    "mr": "eng+mar",
    "kn": "eng+kan",
}


# ---------------------------------------------------------
# Locate Tesseract
# ---------------------------------------------------------
# Windows
if os.name == "nt":
    windows_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(windows_tesseract):
        pytesseract.pytesseract.tesseract_cmd = windows_tesseract

# Linux / Render
else:
    linux_tesseract = shutil.which("tesseract")

    if linux_tesseract:
        pytesseract.pytesseract.tesseract_cmd = linux_tesseract


# ---------------------------------------------------------
# Get language model
# ---------------------------------------------------------
def get_reader(language="en"):
    return LANGUAGE_MODELS.get(language, "eng")


# ---------------------------------------------------------
# Perform OCR
# ---------------------------------------------------------
def perform_ocr(image, language="en"):
    lang = get_reader(language)

    # -----------------------------------------------------
    # Handle PIL Image
    # -----------------------------------------------------
    if hasattr(image, "convert"):
        rgb_image = np.array(image.convert("RGB"))
        input_image = cv2.cvtColor(
            rgb_image,
            cv2.COLOR_RGB2BGR
        )

    # -----------------------------------------------------
    # Handle NumPy / OpenCV image
    # -----------------------------------------------------
    elif hasattr(image, "shape"):
        input_image = image

    # -----------------------------------------------------
    # Handle file path
    # -----------------------------------------------------
    else:
        input_image = cv2.imread(str(image))

    # -----------------------------------------------------
    # Validate image
    # -----------------------------------------------------
    if input_image is None:
        raise ValueError("Unable to read input image.")

    # -----------------------------------------------------
    # Convert to grayscale
    # -----------------------------------------------------
    if len(input_image.shape) == 3:
        gray = cv2.cvtColor(
            input_image,
            cv2.COLOR_BGR2GRAY
        )
    else:
        gray = input_image

    # -----------------------------------------------------
    # Improve text visibility
    # -----------------------------------------------------
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    # -----------------------------------------------------
    # Tesseract OCR
    # -----------------------------------------------------
    data = pytesseract.image_to_data(
        processed,
        lang=lang,
        config="--oem 1 --psm 6",
        output_type=pytesseract.Output.DICT
    )

    # -----------------------------------------------------
    # Collect detected text and confidence
    # -----------------------------------------------------
    lines = []
    confidences = []

    for i, text in enumerate(data["text"]):

        text = str(text).strip()

        try:
            confidence = float(data["conf"][i])
        except (ValueError, TypeError):
            confidence = -1

        if text and confidence >= 0:
            lines.append(text)
            confidences.append(
                confidence / 100.0
            )

    # -----------------------------------------------------
    # Calculate average confidence
    # -----------------------------------------------------
    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    # -----------------------------------------------------
    # Return OCR result
    # -----------------------------------------------------
    return {
        "text": "\n".join(lines),
        "lines": lines,
        "confidence": round(
            average_confidence,
            4
        ),
        "detections": len(lines),
    }