"""
Aadhaar Card Verification System — FastAPI Backend
Runs the full 7-layer fraud detection pipeline and exposes REST endpoints
for the Next.js frontend.
"""

import os
import uuid
import base64
import asyncio
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Pipeline modules
from pipeline.ela_analysis import run_ela
from pipeline.exif_analysis import run_exif_analysis
from pipeline.noise_analysis import run_noise_analysis
from pipeline.forgery_scorer import compute_fraud_score, compute_cross_side_similarity

# Services
from services.yolo_service import run_yolo_detection, crop_field_regions
from services.ocr_service import extract_all_fields
from services.qr_service import decode_qr, cross_validate_ocr_qr
from services.verhoeff import validate_aadhaar

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
ASSETS_DIR = BASE_DIR / "assets"

UPLOADS_DIR.mkdir(exist_ok=True)
(ASSETS_DIR / "ela").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "noise").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "annotated").mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Aadhaar Card Verification API",
    description="7-layer fraud detection: YOLO + PaddleOCR + ELA + Noise + EXIF + QR + Checksum",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated forensic images as static files
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


# ── Helpers ───────────────────────────────────────────────────────────────────
def save_upload(file: UploadFile, prefix: str) -> str:
    """Save uploaded file to uploads/ with a unique name. Returns absolute path."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {ext}")
    unique_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / unique_name
    with open(dest, "wb") as f:
        f.write(file.file.read())
    return str(dest)


def image_to_base64(path: str | None) -> str | None:
    """Convert image file to base64 data URL for embedding in JSON."""
    if not path or not os.path.exists(path):
        return None
    ext = Path(path).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{data}"


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Aadhaar Verification API"}


@app.post("/api/analyze")
async def analyze_card(
    front_image: UploadFile = File(..., description="Front side of Aadhaar card"),
    back_image: UploadFile = File(..., description="Back side of Aadhaar card"),
):
    """
    Full fraud detection pipeline:
    1. Save uploaded images
    2. YOLO field detection on front
    3. PaddleOCR on each detected field
    4. QR decode from back image
    5. Cross-validate OCR ↔ QR
    6. Verhoeff checksum
    7. ELA, Noise, EXIF forensics
    8. Compute weighted fraud score
    9. Return structured JSON response
    """
    front_path = None
    back_path = None

    try:
        # ── Step 1: Save uploads ───────────────────────────────────────────────
        front_path = save_upload(front_image, "front")
        back_path = save_upload(back_image, "back")

        # ── Step 2: YOLO Detection ─────────────────────────────────────────────
        yolo_result = run_yolo_detection(front_path)
        detections = yolo_result.get("detections", [])
        is_tampered = yolo_result.get("is_tampered", False)
        annotated_front_path = yolo_result.get("annotated_image_path")

        # ── Step 3: PaddleOCR on cropped field regions ─────────────────────────
        crops = crop_field_regions(front_path, detections)
        ocr_data = extract_all_fields(crops)

        # ── Step 4: QR Decode (back image) ────────────────────────────────────
        qr_result = decode_qr(back_path)

        # ── Step 5: Cross-Validate OCR ↔ QR ───────────────────────────────────
        qr_mismatches = cross_validate_ocr_qr(ocr_data, qr_result)

        # ── Step 6: Verhoeff Checksum ─────────────────────────────────────────
        aadhaar_number = ocr_data.get("AADHAR_NUMBER", "")
        checksum_result = validate_aadhaar(aadhaar_number)

        # ── Step 7: Forensic Analysis ─────────────────────────────────────────
        # Run ELA and noise on BOTH sides (reference project does this)
        ela_front = run_ela(front_path)
        ela_back = run_ela(back_path)
        noise_front = run_noise_analysis(front_path)
        noise_back = run_noise_analysis(back_path)
        exif_result_front = run_exif_analysis(front_path)
        exif_result_back = run_exif_analysis(back_path)

        # Use the more suspicious EXIF result
        exif_result = exif_result_front if exif_result_front["risk_score"] >= exif_result_back["risk_score"] else exif_result_back

        # ── Step 7b: Cross-Side Similarity ────────────────────────────────────
        cross_side_result = compute_cross_side_similarity(front_path, back_path)

        # ── Step 8: Fraud Scoring ─────────────────────────────────────────────
        yolo_tamper_conf = 0.0
        for det in detections:
            if det["class_name"].lower() == "tampered":
                yolo_tamper_conf = max(yolo_tamper_conf, det["confidence"])

        fraud_result = compute_fraud_score(
            ela_front=ela_front,
            ela_back=ela_back,
            noise_front=noise_front,
            noise_back=noise_back,
            exif_result=exif_result,
            yolo_tamper=is_tampered,
            yolo_tamper_confidence=yolo_tamper_conf,
            qr_mismatches=qr_mismatches,
            checksum_valid=checksum_result["valid"],
            cross_side_result=cross_side_result,
        )

        # ── Step 9: Build Response ────────────────────────────────────────────
        # Convert forensic images to base64 for direct embedding
        ela_image_b64 = image_to_base64(ela_front.get("ela_image_path"))
        ela_back_b64 = image_to_base64(ela_back.get("ela_image_path"))
        noise_heatmap_b64 = image_to_base64(noise_front.get("heatmap_path"))
        noise_back_b64 = image_to_base64(noise_back.get("heatmap_path"))
        annotated_front_b64 = image_to_base64(annotated_front_path)

        return JSONResponse(content={
            "status": "success",

            # Overall result
            "fraud_score": fraud_result["final_score"],
            "risk_level": fraud_result["risk_level"],
            "fraud_indicators": fraud_result["fraud_indicators"],
            "score_breakdown": fraud_result["breakdown"],

            # OCR Extracted Fields
            "ocr_data": {
                "name": ocr_data.get("NAME", ""),
                "aadhaar_number": ocr_data.get("AADHAR_NUMBER", ""),
                "gender": ocr_data.get("GENDER", ""),
                "date_of_birth": ocr_data.get("DATE_OF_BIRTH", ""),
                "address": ocr_data.get("ADDRESS", ""),
            },

            # QR Code Data
            "qr_data": {
                "decoded": "error" not in qr_result,
                "qr_type": qr_result.get("qr_type", "unknown"),
                "name": qr_result.get("name", ""),
                "dob": qr_result.get("dob", ""),
                "gender": qr_result.get("gender", ""),
                "address": qr_result.get("address", ""),
                "error": qr_result.get("error"),
            },

            # Validation results
            "qr_mismatches": qr_mismatches,
            "checksum": {
                "valid": checksum_result["valid"],
                "reason": checksum_result["reason"],
                "number": checksum_result.get("clean_number", ""),
            },

            # YOLO Detection
            "yolo": {
                "detection_count": yolo_result.get("detection_count", 0),
                "average_confidence": yolo_result.get("average_confidence", 0.0),
                "is_tampered": is_tampered,
                "detections": detections,
                "annotated_image": annotated_front_b64,
            },

            # Forensic Analysis — dual side
            "forensics": {
                "ela": {
                    "risk_score": round((ela_front.get("risk_score", 0) + ela_back.get("risk_score", 0)) / 2, 1),
                    "front": {
                        "risk_score": ela_front.get("risk_score", 0),
                        "mean_intensity": ela_front.get("mean_intensity"),
                        "global_variance": ela_front.get("global_variance"),
                        "image": ela_image_b64,
                    },
                    "back": {
                        "risk_score": ela_back.get("risk_score", 0),
                        "image": ela_back_b64,
                    },
                    "error": ela_front.get("error"),
                },
                "noise": {
                    "risk_score": round((noise_front.get("risk_score", 0) + noise_back.get("risk_score", 0)) / 2, 1),
                    "front": {
                        "risk_score": noise_front.get("risk_score", 0),
                        "suspicious_region_ratio": noise_front.get("suspicious_region_ratio"),
                        "heatmap": noise_heatmap_b64,
                    },
                    "back": {
                        "risk_score": noise_back.get("risk_score", 0),
                        "heatmap": noise_back_b64,
                    },
                    "error": noise_front.get("error"),
                },
                "exif": {
                    "risk_score": exif_result.get("risk_score", 0),
                    "software_detected": exif_result.get("software_detected"),
                    "camera_make": exif_result.get("camera_make"),
                    "camera_model": exif_result.get("camera_model"),
                    "reasons": exif_result.get("reasons", []),
                    "raw_fields": exif_result.get("raw_fields", {}),
                },
                "cross_side": {
                    "risk_score": cross_side_result.get("risk_score", 0),
                    "available": cross_side_result.get("available", False),
                    "reason": cross_side_result.get("reason", ""),
                    "correlation": cross_side_result.get("correlation"),
                },
            },
            "forensic_decision": fraud_result.get("forensic_decision"),
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Clean up uploaded temp files
        for path in [front_path, back_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
