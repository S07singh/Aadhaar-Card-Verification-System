"""
OCR Service — Uses PaddleOCR for bilingual (English + Hindi) text extraction
from cropped Aadhaar field regions detected by YOLO.
"""

import re
import numpy as np
from paddleocr import PaddleOCR

# Initialize PaddleOCR once (English + Hindi bilingual)
_ocr_engine: PaddleOCR | None = None


def get_ocr_engine() -> PaddleOCR:
    """Lazy-initialize PaddleOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        print("[OCR] Initializing PaddleOCR (English + Hindi)...")
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang="en",          # Primary: English
            use_gpu=False,      # Set True if CUDA available
            show_log=False,
        )
        print("[OCR] PaddleOCR ready.")
    return _ocr_engine


def extract_text_from_crop(crop: np.ndarray) -> str:
    """
    Runs PaddleOCR on a numpy image array (BGR, from OpenCV).
    Returns the extracted text as a single cleaned string.
    """
    if crop is None or crop.size == 0:
        return ""

    try:
        ocr = get_ocr_engine()
        # PaddleOCR expects RGB or file path
        import cv2
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        result = ocr.ocr(rgb_crop, cls=True)

        if not result or not result[0]:
            return ""

        lines = []
        for line in result[0]:
            if line and len(line) >= 2:
                text, confidence = line[1]
                if confidence > 0.4:  # Confidence threshold
                    lines.append(str(text).strip())

        return " ".join(lines).strip()
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


def extract_all_fields(crops: dict[str, np.ndarray]) -> dict[str, str]:
    """
    Extract OCR text from all cropped field regions.
    Applies field-specific post-processing.

    Args:
        crops: {field_name: numpy_image_array}

    Returns:
        {field_name: extracted_text}
    """
    extracted = {}

    for field_name, crop in crops.items():
        raw_text = extract_text_from_crop(crop)

        if field_name == "AADHAR_NUMBER":
            raw_text = _clean_aadhaar_number(raw_text)
        elif field_name == "DATE_OF_BIRTH":
            raw_text = _clean_date(raw_text)
        elif field_name == "GENDER":
            raw_text = _clean_gender(raw_text)
        elif field_name == "NAME":
            raw_text = _clean_name(raw_text)

        extracted[field_name] = raw_text

    return extracted


def _clean_aadhaar_number(text: str) -> str:
    """Extract only digits from Aadhaar number field."""
    digits = re.sub(r"[^0-9]", "", text)
    # Aadhaar is 12 digits — try to extract exactly 12
    if len(digits) >= 12:
        return digits[:12]
    return digits


def _clean_date(text: str) -> str:
    """Normalize date format."""
    # Try to find dd/mm/yyyy or dd-mm-yyyy pattern
    match = re.search(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", text)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = "19" + y if int(y) > 25 else "20" + y
        return f"{d.zfill(2)}/{m.zfill(2)}/{y}"
    return text.strip()


def _clean_gender(text: str) -> str:
    """Normalize gender to MALE / FEMALE / TRANSGENDER."""
    t = text.upper()
    if "MALE" in t or "M" == t.strip():
        return "MALE"
    if "FEMALE" in t or "F" == t.strip():
        return "FEMALE"
    if "TRANSGENDER" in t:
        return "TRANSGENDER"
    return text.strip()


def _clean_name(text: str) -> str:
    """Remove stray numbers and clean name text."""
    # Remove lines that are purely numeric
    lines = [l for l in text.split("\n") if not l.strip().isdigit()]
    return " ".join(lines).strip()
