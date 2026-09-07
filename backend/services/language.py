import re
from langdetect import detect, LangDetectException

SCRIPT_PATTERNS = {
    "kn": re.compile(r"[\u0C80-\u0CFF]"),
    "hi": re.compile(r"[\u0900-\u097F]"),
    "mr": re.compile(r"[\u0900-\u097F]"),
}


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "en"

    kannada = len(SCRIPT_PATTERNS["kn"].findall(text))
    devanagari = len(SCRIPT_PATTERNS["hi"].findall(text))

    if kannada >= 2:
        return "kn"

    if devanagari >= 2:
        # Hindi and Marathi both use Devanagari. langdetect is used as a
        # secondary signal, but "hi" is the safe default for Devanagari OCR.
        try:
            detected = detect(text)
            return "mr" if detected == "mr" else "hi"
        except LangDetectException:
            return "hi"

    try:
        detected = detect(text)
        if detected in {"en", "hi", "mr", "kn"}:
            return detected
    except LangDetectException:
        pass

    return "en"
