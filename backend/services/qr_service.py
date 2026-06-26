"""
QR Service — Decodes the Aadhaar secure QR code from the back of the card.
Uses pyzbar for QR decoding and pyaadhaar for parsing the secure QR format.
"""

import cv2
import numpy as np
from pyzbar.pyzbar import decode as pyzbar_decode

try:
    from pyaadhaar.utils import isSecureQr
    from pyaadhaar.decode import AadhaarSecureQr
    PYAADHAAR_AVAILABLE = True
except ImportError:
    PYAADHAAR_AVAILABLE = False
    print("[QR] Warning: pyaadhaar not installed. QR decoding limited.")


def _try_decode_image(img_variant) -> list:
    """Try pyzbar decode on an image variant, return list of codes."""
    try:
        return pyzbar_decode(img_variant) or []
    except Exception:
        return []


def decode_qr(image_path: str) -> dict:
    """
    Decodes the Aadhaar QR code from the back side image.
    Tries multiple preprocessing strategies to handle low-res or small QR codes.

    Returns dict with QR data or an error key.
    Attempts Secure QR first, falls back to plain text QR.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not read image"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Strategy 1: Raw grayscale
        codes = _try_decode_image(gray)

        # Strategy 2: OTSU threshold (binarize)
        if not codes:
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            codes = _try_decode_image(thresh)

        # Strategy 3: 2x upscale (helps with small/low-res QR codes)
        if not codes:
            h, w = gray.shape
            upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            codes = _try_decode_image(upscaled)

        # Strategy 4: Upscale + sharpen
        if not codes:
            h, w = gray.shape
            upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(upscaled, -1, kernel)
            codes = _try_decode_image(sharpened)

        # Strategy 5: Adaptive threshold (handles uneven lighting)
        if not codes:
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            codes = _try_decode_image(adaptive)

        if not codes:
            return {"error": "No QR code found in image"}

        qr_data = codes[0].data

        # Try Secure QR (numeric, > 100 digits)
        if PYAADHAAR_AVAILABLE:
            try:
                if isSecureQr(qr_data):
                    secure_qr = AadhaarSecureQr(int(qr_data))
                    decoded = secure_qr.decodeddata()
                    if decoded:
                        return {
                            "qr_type": "secure",
                            "name": decoded.get("name", ""),
                            "dob": decoded.get("dob", ""),
                            "gender": decoded.get("gender", ""),
                            "address": decoded.get("address", ""),
                            "aadhaar_last4": decoded.get("last4", ""),
                            "raw": decoded,
                        }
            except Exception as e:
                print(f"[QR] Secure QR parsing failed: {e}")

        # Fallback: plain text / XML QR
        try:
            text = qr_data.decode("utf-8")
            return {"qr_type": "plain", "raw_text": text, "error": None}
        except Exception:
            return {"error": "QR data could not be decoded as text"}

    except Exception as e:
        return {"error": str(e)}


def cross_validate_ocr_qr(ocr_data: dict, qr_data: dict) -> list[str]:
    """
    Cross-validates OCR extracted fields against QR code data.
    Returns list of field names where there is a mismatch.
    """
    mismatches = []

    if "error" in qr_data or qr_data.get("qr_type") == "plain":
        return mismatches  # Can't validate without structured QR data

    def normalize(s: str) -> str:
        return str(s).lower().strip().replace(" ", "").replace("-", "").replace("/", "")

    # Name check
    ocr_name = normalize(ocr_data.get("NAME", ""))
    qr_name = normalize(qr_data.get("name", ""))
    if ocr_name and qr_name and ocr_name not in qr_name and qr_name not in ocr_name:
        mismatches.append("Name")

    # DOB check
    ocr_dob = normalize(ocr_data.get("DATE_OF_BIRTH", ""))
    qr_dob = normalize(qr_data.get("dob", ""))
    if ocr_dob and qr_dob and ocr_dob != qr_dob:
        mismatches.append("Date of Birth")

    # Gender check
    ocr_gender = normalize(ocr_data.get("GENDER", ""))
    qr_gender = normalize(qr_data.get("gender", ""))
    if ocr_gender and qr_gender and ocr_gender not in qr_gender and qr_gender not in ocr_gender:
        mismatches.append("Gender")

    return mismatches
