from pathlib import Path
import cv2
import numpy as np


def _deskew(gray):
    # Use only when a meaningful foreground angle is detected.
    inv = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(inv > 30))
    if len(coords) < 100:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) > 8:
        return gray

    h, w = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_image(image_path: str):
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Unable to read image.")

    # Upscale small handwriting before OCR.
    h, w = image.shape[:2]
    scale = 2.0 if max(h, w) < 1800 else 1.5
    up = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    gray = _deskew(gray)

    # Light denoising; avoid aggressive thresholding because handwriting strokes
    # can be damaged by hard binarization.
    gray = cv2.fastNlMeansDenoising(gray, None, 7, 7, 21)

    return gray
