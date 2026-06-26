"""
EXIF Metadata Forensics — Checks for editing software traces, timestamp anomalies,
missing camera info, and other signs of digital manipulation.
"""

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


SUSPICIOUS_SOFTWARE = [
    "photoshop", "gimp", "canva", "snapseed",
    "pixlr", "lightroom", "editor", "paint",
    "affinity", "inkscape", "corel"
]


def run_exif_analysis(image_path: str) -> dict:
    """
    Extracts and analyses EXIF metadata for fraud signals.
    Returns a risk score + structured findings.
    """
    risk = 0
    reasons = []
    raw_fields = {}

    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()

        if not exif_raw:
            return {
                "risk_score": 50,
                "reasons": ["Metadata stripped or missing — common after editing"],
                "raw_fields": {},
                "software_detected": None,
                "camera_make": None,
                "camera_model": None,
            }

        exif = {}
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, str(tag_id))
            exif[tag] = value
            # Only include string-serializable values
            try:
                raw_fields[str(tag)] = str(value)
            except Exception:
                pass

        # 1. Editing software detection
        software = str(exif.get("Software", "")).strip()
        software_detected = None
        if software:
            for tool in SUSPICIOUS_SOFTWARE:
                if tool in software.lower():
                    risk += 60
                    reasons.append(f"Editing software detected: {software}")
                    software_detected = software
                    break

        # 2. Timestamp anomaly
        create_time = exif.get("DateTimeOriginal")
        modify_time = exif.get("DateTime")

        if create_time and modify_time:
            if create_time != modify_time:
                risk += 20
                reasons.append("Creation and modification timestamps mismatch")
            try:
                create_dt = datetime.strptime(str(create_time), "%Y:%m:%d %H:%M:%S")
                if create_dt.year < 2000 or create_dt.year > datetime.now().year:
                    risk += 15
                    reasons.append(f"Abnormal creation date: {create_dt.year}")
            except Exception:
                pass
        elif not create_time and not modify_time:
            risk += 10
            reasons.append("No timestamp metadata found")

        # 3. Camera info
        make = exif.get("Make")
        model_cam = exif.get("Model")
        if not make or not model_cam:
            risk += 15
            reasons.append("Camera make/model information missing")

        # 4. GPS
        if "GPSInfo" not in exif:
            risk += 10
            reasons.append("GPS metadata missing")

        return {
            "risk_score": min(risk, 100),
            "reasons": reasons,
            "software_detected": software_detected,
            "camera_make": str(make) if make else None,
            "camera_model": str(model_cam) if model_cam else None,
            "raw_fields": raw_fields,
        }

    except Exception as e:
        return {
            "risk_score": 40,
            "reasons": [f"EXIF parsing error: {str(e)}"],
            "raw_fields": {},
            "software_detected": None,
            "camera_make": None,
            "camera_model": None,
        }
