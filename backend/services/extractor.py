import re
from typing import Dict, List, Optional


# ============================================================
# Regional-language field labels
# ============================================================

FIELD_LABELS = {
    "name": [
        "name",
        "full name",
        "नाम",
        "नाव",
        "नांव",
        "व्यक्तिगत जानकारी",
        "व्यक्तिगत माहिती",
        "ಹೆಸರು",
    ],
    "phone": [
        "phone",
        "mobile",
        "mobile number",
        "phone number",
        "contact",
        "फोन",
        "मोबाइल",
        "मोबाईल",
        "दूरध्वनी",
        "दूरभाष",
        "दूरवाणी",
        "ದೂರವಾಣಿ",
        "ಮೊಬೈಲ್",
    ],
    "email": [
        "email",
        "e-mail",
        "ईमेल",
        "इमेल",
        "ई-मेल",
        "ईमेल आयडी",
        "ईमेल पता",
        "इमेल",
        "ईमेल",
        "ಇಮೇಲ್",
    ],
    "date": [
        "date",
        "दिनांक",
        "दिनांक :",
        "तारीख",
        "दिनांक",
        "दिनांक :",
        "ದಿನಾಂಕ",
    ],
    "amount": [
        "amount",
        "price",
        "cost",
        "total",
        "राशि",
        "रक्कम",
        "एकूण",
        "मूल्य",
        "ಮೊತ್ತ",
        "ಬೆಲೆ",
        "ಒಟ್ಟು",
    ],
    "address": [
        "address",
        "पता",
        "पत्ता",
        "पत्ताः",
        "पत्ता :",
        "विस्तार",
        "ವಿಳಾಸ",
    ],
    "pin_code": [
        "pin",
        "pin code",
        "pincode",
        "postal code",
        "zip",
        "पिन",
        "पिन कोड",
        "पिनकोड",
        "पिन कोड :",
        "पिनकोड :",
        "पिन कोड",
        "पिनकोड",
        "पिन कोड",
        "ಪಿನ್",
        "ಪಿನ್ ಕೋಡ್",
        "ಪಿನ್ ಕೋಡ್ :",
    ],
    "organization": [
        "organization",
        "organisation",
        "company",
        "office",
        "संस्था",
        "कंपनी",
        "कम्पनी",
        "संघटना",
        "कंपनीचे नाव",
        "ಸಂಸ್ಥೆ",
        "ಕಂಪನಿ",
    ],
}


# ============================================================
# Common OCR corrections
# IMPORTANT:
# These corrections are used only in contexts where they are
# reasonably safe, such as email / numeric fields.
# ============================================================

def normalize_spaces(text: str) -> str:
    """Normalize whitespace while preserving line structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return text.strip()


def clean_value(value: str) -> str:
    """Clean an extracted field value."""
    if not value:
        return ""

    value = value.strip()

    # Remove common separator characters from beginning/end.
    value = re.sub(r"^[\s:：=\-–—|,;]+", "", value)
    value = re.sub(r"[\s:：=\-–—|,;]+$", "", value)

    return value.strip()


def canonical_label_match(line: str, labels: List[str]) -> bool:
    """
    Check whether a line contains one of the supplied field labels.
    This works with English and Unicode regional-language labels.
    """
    normalized = line.strip().lower()

    for label in labels:
        label_norm = label.strip().lower()

        if normalized == label_norm:
            return True

        # Label followed by punctuation/value.
        pattern = r"^" + re.escape(label_norm) + r"\s*[:：=\-]?"
        if re.search(pattern, normalized, re.IGNORECASE):
            return True

    return False


def extract_value_after_label(
    lines: List[str],
    labels: List[str],
    max_following_lines: int = 2
) -> str:
    """
    Find a field label and return the value appearing:
    1. on the same line, or
    2. on one of the following lines.

    This is important because handwriting OCR frequently produces:

        Amount:
        Rs
        12500

    instead of:

        Amount: Rs 12500
    """

    for index, original_line in enumerate(lines):
        line = original_line.strip()

        if not line:
            continue

        lower_line = line.lower()

        for label in labels:
            label_lower = label.lower()

            # ------------------------------------------------
            # Same-line extraction
            # ------------------------------------------------
            if lower_line.startswith(label_lower):
                remainder = line[len(label):]

                remainder = re.sub(
                    r"^\s*[:：=\-–—]\s*",
                    "",
                    remainder
                ).strip()

                if remainder:
                    return clean_value(remainder)

                # ------------------------------------------------
                # Value on following line(s)
                # ------------------------------------------------
                for offset in range(1, max_following_lines + 1):
                    next_index = index + offset

                    if next_index >= len(lines):
                        break

                    candidate = clean_value(lines[next_index])

                    if candidate and not canonical_label_match(
                        candidate,
                        sum(FIELD_LABELS.values(), [])
                    ):
                        return candidate

    return ""


# ============================================================
# Phone extraction
# ============================================================

def extract_phone(text: str) -> str:
    """
    Extract Indian-style 10-digit phone numbers.

    Handles common OCR formatting:
        9876543210
        98765 43210
        9876-543210
        Phone:
        9876543210
    """

    # First remove obvious phone separators.
    candidates = re.findall(
        r"(?<!\d)(?:\+91[\s\-]?)?(\d[\d\s\-]{8,14}\d)(?!\d)",
        text
    )

    for candidate in candidates:
        digits = re.sub(r"\D", "", candidate)

        if len(digits) == 10 and digits[0] in "6789":
            return digits

        if len(digits) == 12 and digits.startswith("91"):
            number = digits[-10:]

            if number[0] in "6789":
                return number

    # Look specifically around phone/mobile labels.
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if any(label.lower() in line.lower() for label in FIELD_LABELS["phone"]):
            nearby = "\n".join(lines[i:i + 3])

            digit_groups = re.findall(r"\d[\d\s\-]{8,14}\d", nearby)

            for group in digit_groups:
                digits = re.sub(r"\D", "", group)

                if len(digits) == 10 and digits[0] in "6789":
                    return digits

    return ""


# ============================================================
# Email extraction
# ============================================================

def normalize_email_candidate(candidate: str) -> str:
    """
    Repair common OCR email problems.

    Examples:
        rahul.sharma@example com
        rahul.sharma@example..com
        rahul.sharma @ example.com
        rahul sharma@example.com
    """

    candidate = candidate.strip()

    # Remove spaces around @ and dots.
    candidate = re.sub(r"\s*@\s*", "@", candidate)
    candidate = re.sub(r"\s*\.\s*", ".", candidate)

    # Remove spaces from the local part.
    if "@" in candidate:
        local, domain = candidate.split("@", 1)
        local = re.sub(r"\s+", "", local)
        domain = re.sub(r"\s+", "", domain)
        candidate = local + "@" + domain

    # Common OCR confusion.
    candidate = re.sub(r"\.cow$", ".com", candidate, flags=re.I)
    candidate = re.sub(r"\.con$", ".com", candidate, flags=re.I)
    candidate = re.sub(r"\.corn$", ".com", candidate, flags=re.I)

    # Remove repeated dots.
    candidate = re.sub(r"\.{2,}", ".", candidate)

    return candidate.strip(".,;: ")


def extract_email(text: str) -> str:
    """
    OCR-tolerant email extraction.
    """

    normalized = text.replace("\n", " ")

    # Normal case.
    match = re.search(
        r"[A-Za-z0-9._%+\-\s]+@[A-Za-z0-9.\-\s]+\.[A-Za-z]{2,}",
        normalized
    )

    if match:
        candidate = normalize_email_candidate(match.group(0))

        if "@" in candidate and "." in candidate.split("@")[-1]:
            return candidate

    # OCR often separates ".com":
    # rahul.sharma@example com
    match = re.search(
        r"([A-Za-z0-9._%+\-\s]+@[A-Za-z0-9.\-\s]+)\s+"
        r"(com|in|org|net|co\.in)\b",
        normalized,
        flags=re.I
    )

    if match:
        candidate = (
            match.group(1).strip() + "." + match.group(2).strip()
        )

        candidate = normalize_email_candidate(candidate)

        if "@" in candidate:
            return candidate

    return ""


# ============================================================
# Date extraction
# ============================================================

def extract_date(text: str) -> str:
    """
    Detect common date formats:
        30/08/2026
        30-08-2026
        30.08.2026
        30/08/26
    """

    patterns = [
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}\b",
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2}\b",
    ]

    # Prefer dates close to a date label.
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if any(label.lower() in line.lower() for label in FIELD_LABELS["date"]):
            nearby = "\n".join(lines[i:i + 3])

            for pattern in patterns:
                match = re.search(pattern, nearby)

                if match:
                    return match.group(0)

    # Fallback: search entire OCR text.
    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(0)

    return ""


# ============================================================
# Amount extraction
# ============================================================

def extract_amount(text: str) -> str:
    """
    Extract amounts from formats such as:

        Rs 12500
        ₹ 12,500
        INR 12500
        Amount:
        Rs
        12500
    """

    currency_prefix = r"(?:rs\.?|inr|₹)\s*"

    # Currency + number.
    match = re.search(
        currency_prefix + r"(\d[\d,]*(?:\.\d{1,2})?)",
        text,
        flags=re.I
    )

    if match:
        return match.group(1).replace(",", "")

    # Look around amount labels.
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if any(label.lower() in line.lower() for label in FIELD_LABELS["amount"]):
            nearby = "\n".join(lines[i:i + 4])

            match = re.search(
                currency_prefix + r"(\d[\d,]*(?:\.\d{1,2})?)",
                nearby,
                flags=re.I
            )

            if match:
                return match.group(1).replace(",", "")

            # Currency and amount may be separated by OCR.
            numbers = re.findall(r"\b\d[\d,]*(?:\.\d{1,2})?\b", nearby)

            if numbers:
                # Prefer the largest reasonable numeric value.
                cleaned = [
                    n.replace(",", "")
                    for n in numbers
                ]

                cleaned = [
                    n for n in cleaned
                    if len(re.sub(r"\D", "", n)) >= 3
                ]

                if cleaned:
                    return max(cleaned, key=lambda x: float(x))

    return ""


# ============================================================
# PIN code extraction
# ============================================================

def extract_pin(text: str) -> str:
    """
    Extract a six-digit Indian PIN code.

    Uses label context first and then whole-text fallback.
    """

    lines = text.splitlines()

    # First look near PIN labels.
    for i, line in enumerate(lines):
        if any(label.lower() in line.lower() for label in FIELD_LABELS["pin_code"]):
            nearby = "\n".join(lines[i:i + 3])

            matches = re.findall(r"(?<!\d)\d{6}(?!\d)", nearby)

            if matches:
                return matches[0]

    # Whole document fallback.
    matches = re.findall(r"(?<!\d)\d{6}(?!\d)", text)

    if matches:
        return matches[-1]

    return ""


# ============================================================
# Address extraction
# ============================================================

def extract_address(text: str) -> str:
    """
    Extract address from a labelled section.

    Address may span several lines, so we collect up to a few
    lines after the label.
    """

    lines = [line.strip() for line in text.splitlines()]

    for i, line in enumerate(lines):
        if any(label.lower() in line.lower() for label in FIELD_LABELS["address"]):

            values = []

            # Same-line value.
            value = extract_value_after_label(
                lines[i:i + 1],
                FIELD_LABELS["address"],
                max_following_lines=0
            )

            if value:
                values.append(value)

            # Following lines.
            for j in range(i + 1, min(i + 5, len(lines))):
                candidate = clean_value(lines[j])

                if not candidate:
                    continue

                # Stop when another known field begins.
                if any(
                    canonical_label_match(
                        candidate,
                        FIELD_LABELS[field]
                    )
                    for field in FIELD_LABELS
                    if field != "address"
                ):
                    break

                values.append(candidate)

            if values:
                return ", ".join(values)

    return ""


# ============================================================
# Organization extraction
# ============================================================

def extract_organization(text: str) -> str:
    lines = text.splitlines()

    return extract_value_after_label(
        lines,
        FIELD_LABELS["organization"],
        max_following_lines=2
    )


# ============================================================
# Name extraction
# ============================================================

def extract_name(text: str) -> str:
    """
    Extract name using explicit name labels first.

    Also avoids returning the label itself, which was happening
    in some Hindi/Marathi/Kannada OCR results.
    """

    lines = text.splitlines()

    # --------------------------------------------------------
    # 1. Explicit name label
    # --------------------------------------------------------
    value = extract_value_after_label(
        lines,
        FIELD_LABELS["name"],
        max_following_lines=2
    )

    if value:
        return value

    # --------------------------------------------------------
    # 2. Look for common English-style "Name: Rahul Sharma"
    # --------------------------------------------------------
    for line in lines:
        match = re.search(
            r"(?:name|full\s+name)\s*[:：=\-]\s*(.+)",
            line,
            flags=re.I
        )

        if match:
            value = clean_value(match.group(1))

            if value:
                return value

    # --------------------------------------------------------
    # 3. Fallback:
    # If the OCR starts with a plausible Latin name, use it.
    # --------------------------------------------------------
    for line in lines[:5]:
        candidate = clean_value(line)

        if not candidate:
            continue

        # Don't return obvious labels.
        if any(
            candidate.lower() == label.lower()
            for label in FIELD_LABELS["name"]
        ):
            continue

        # Avoid lines containing digits.
        if re.search(r"\d", candidate):
            continue

        # Latin alphabet name fallback.
        if re.fullmatch(
            r"[A-Za-z]+(?:[\s][A-Za-z]+){1,3}",
            candidate
        ):
            return candidate

    return ""


# ============================================================
# Keyword extraction
# ============================================================

def extract_keywords(text: str) -> List[str]:
    """
    Extract useful Latin-script keywords.

    Regional-language text is retained in OCR output but
    keyword extraction focuses on searchable Latin terms.
    """

    words = re.findall(r"\b[A-Za-z][A-Za-z0-9._-]{2,}\b", text.lower())

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "name",
        "phone",
        "mobile",
        "email",
        "date",
        "amount",
        "address",
        "code",
        "pin",
        "number",
        "example",
        "com",
    }

    result = []

    for word in words:
        if word in stop_words:
            continue

        if word not in result:
            result.append(word)

    return result[:20]


# ============================================================
# Main extraction function
# ============================================================

def extract_information(text: str, language: Optional[str] = None) -> Dict:
    """
    Main information extraction pipeline.

    Compatible with the existing Flask application.

    Returns:
        address
        amount
        date
        email
        keywords
        language
        name
        organization
        phone
        pin_code
    """

    if not text:
        text = ""

    text = normalize_spaces(text)

    result = {
        "address": "",
        "amount": "",
        "date": "",
        "email": "",
        "keywords": [],
        "language": language or "",
        "name": "",
        "organization": "",
        "phone": "",
        "pin_code": "",
    }

    # Main extraction.
    result["name"] = extract_name(text)
    result["phone"] = extract_phone(text)
    result["email"] = extract_email(text)
    result["date"] = extract_date(text)
    result["amount"] = extract_amount(text)
    result["address"] = extract_address(text)
    result["organization"] = extract_organization(text)
    result["pin_code"] = extract_pin(text)
    result["keywords"] = extract_keywords(text)

    return result


# ============================================================
# Backward-compatible alias
# ============================================================

def extract_fields(text: str, language: Optional[str] = None) -> Dict:
    """
    Backward-compatible wrapper in case another part of the
    project calls extract_fields().
    """
    return extract_information(text, language)