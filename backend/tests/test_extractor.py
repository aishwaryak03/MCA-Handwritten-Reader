from services.extractor import extract_information


def test_clean_extraction():
    text = """
    Name: Rahul Sharma
    Phone: 9876543210
    Email: rahul.sharma@example.com
    Date: 12/08/2026
    Amount: Rs 12500
    PIN: 411001
    Address: Pune, Maharashtra
    Organization: ABC Technologies
    """
    data = extract_information(text)

    assert data["name"] == "Rahul Sharma"
    assert data["phone"] == "9876543210"
    assert data["email"] == "rahul.sharma@example.com"
    assert data["date"] == "12/08/2026"
    assert data["amount"] == "12500"
    assert data["pin_code"] == "411001"
    assert data["address"] == "Pune, Maharashtra"


def test_split_amount():
    text = """
    Name: Rahul Sharma
    Amount:
    Rs
    12500
    """
    data = extract_information(text)
    assert data["amount"] == "12500"


def test_ocr_tolerant_email():
    text = "Email: rahul sharma@example.cow"
    data = extract_information(text)
    assert data["email"] == "rahulsharma@example.com"
