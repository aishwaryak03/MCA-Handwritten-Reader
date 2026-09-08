from functools import lru_cache
from pathlib import Path
import numpy as np

MODEL_DIR = Path(__file__).resolve().parents[1] / "easyocr_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

LANGUAGE_MODELS = {
    "en": ["en"],
    "hi": ["en", "hi"],
    "mr": ["en", "mr"],
    "kn": ["en", "kn"],
}


@lru_cache(maxsize=4)
def get_reader(language="en"):
    import easyocr
    language = language if language in LANGUAGE_MODELS else "en"
    return easyocr.Reader(LANGUAGE_MODELS[language], gpu=False, model_storage_directory=str(MODEL_DIR))


def perform_ocr(image, language="en"):
    reader = get_reader(language)

    if hasattr(image, "shape"):
        input_image = image
    else:
        input_image = str(image)

    results = reader.readtext(
        input_image,
        detail=1,
        paragraph=False,
        contrast_ths=0.08,
        adjust_contrast=0.6,
        mag_ratio=1.5,
        text_threshold=0.45,
        low_text=0.25,
        link_threshold=0.25,
        canvas_size=3000,
        rotation_info=[90, 180, 270],
    )

    lines = []
    confidences = []

    for item in results:
        if len(item) != 3:
            continue
        _, text, confidence = item
        text = str(text).strip()
        if text:
            lines.append(text)
            confidences.append(float(confidence))

    average_confidence = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )

    return {
        "text": "\n".join(lines),
        "lines": lines,
        "confidence": round(average_confidence, 4),
        "detections": len(lines),
    }


