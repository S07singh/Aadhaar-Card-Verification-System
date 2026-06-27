"""
Fraud Scorer — Combines ELA (front+back), Noise (front+back), EXIF,
YOLO tamper detection, Cross-Side similarity, QR-OCR mismatch, and
Verhoeff checksum into a final weighted score with conditional boosts.
Matches the 7-layer logic of the reference project.
"""

import cv2
import numpy as np

from typing import Any


# Weights for each forensic signal
WEIGHTS = {
    "ela": 0.30,
    "noise": 0.26,
    "yolo_tamper": 0.17,
    "exif": 0.09,
    "cross_side": 0.18,
}


def compute_cross_side_similarity(front_path: str, back_path: str) -> dict:
    """
    Compares front vs back card images. If they look nearly identical,
    it's a strong fraud signal (someone used the same image for both sides).
    """
    try:
        front = cv2.imread(front_path, cv2.IMREAD_GRAYSCALE)
        back = cv2.imread(back_path, cv2.IMREAD_GRAYSCALE)
        if front is None or back is None:
            return {"risk_score": 0.0, "available": False, "reason": "Could not read images"}

        target = (512, 320)
        front = cv2.resize(front, target, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        back = cv2.resize(back, target, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0

        # Pixel correlation
        corr = float(np.corrcoef(front.flatten(), back.flatten())[0, 1]) if (front.std() > 1e-6 and back.std() > 1e-6) else 0.0

        # Histogram similarity
        h_front = cv2.calcHist([np.uint8(front * 255)], [0], None, [64], [0, 256])
        h_back = cv2.calcHist([np.uint8(back * 255)], [0], None, [64], [0, 256])
        hist_corr = float(cv2.compareHist(h_front, h_back, cv2.HISTCMP_CORREL))

        mad = float(np.mean(np.abs(front - back)))

        if corr >= 0.97 and hist_corr >= 0.90 and mad <= 0.03:
            risk_score, reason = 95.0, "Front and back images are near-identical — very suspicious"
        elif corr >= 0.90 and hist_corr >= 0.75 and mad <= 0.06:
            risk_score, reason = 80.0, "Front and back images are highly similar"
        elif corr >= 0.78 and hist_corr >= 0.45 and mad <= 0.10:
            risk_score, reason = 55.0, "Front and back images are unusually similar"
        else:
            risk_score, reason = 8.0, "Front and back show expected visual differences"

        return {
            "risk_score": round(risk_score, 2),
            "available": True,
            "correlation": round(corr, 4),
            "histogram_correlation": round(hist_corr, 4),
            "mean_abs_difference": round(mad, 4),
            "reason": reason,
        }
    except Exception as e:
        return {"risk_score": 0.0, "available": False, "reason": str(e)}


def _classify_risk(score: float) -> str:
    if score >= 67:
        return "Likely Forged"
    if score >= 42:
        return "Needs Manual Review"
    return "Likely Authentic"


def compute_fraud_score(
    ela_front: dict,
    ela_back: dict,
    noise_front: dict,
    noise_back: dict,
    exif_result: dict,
    yolo_tamper: bool,
    yolo_tamper_confidence: float,
    qr_mismatches: list[str],
    checksum_valid: bool,
    cross_side_result: dict | None = None,
) -> dict:
    """
    Computes a final weighted fraud score (0–100) and risk level.
    Runs ELA and Noise on both sides, averages them.
    Applies conditional boosts when multiple signals align.
    """
    # Average ELA and noise across both card sides
    ela_score = float(np.mean([
        min(float(ela_front.get("risk_score", 0)), 100.0),
        min(float(ela_back.get("risk_score", 0)), 100.0),
    ]))
    noise_score = float(np.mean([
        min(float(noise_front.get("risk_score", 0)), 100.0),
        min(float(noise_back.get("risk_score", 0)), 100.0),
    ]))
    exif_score = min(float(exif_result.get("risk_score", 50)), 100.0)

    # YOLO tamper — strong confidence gets higher score
    if yolo_tamper:
        yolo_score = min(55.0 + yolo_tamper_confidence * 35.0, 100.0)
    else:
        yolo_score = 6.0

    # Cross-side similarity
    cross_score = 0.0
    cross_reason = ""
    if cross_side_result:
        cross_score = min(float(cross_side_result.get("risk_score", 0)), 100.0)
        cross_reason = cross_side_result.get("reason", "")


    checksum_score = 0.0 if checksum_valid else 100.0

    # --- Base weighted score ---
    base_score = float(np.clip(
        ela_score * WEIGHTS["ela"] +
        noise_score * WEIGHTS["noise"] +
        yolo_score * WEIGHTS["yolo_tamper"] +
        exif_score * WEIGHTS["exif"] +
        cross_score * WEIGHTS["cross_side"],
        0.0, 100.0
    ))

    # --- Conditional boosts (when multiple signals align) ---
    boost = 0.0
    if ela_score >= 60 and noise_score >= 55:
        boost += 12.0  # Both forensics elevated
    if yolo_tamper and (ela_score >= 50 or noise_score >= 50):
        boost += 8.0   # Tamper confirmed by forensics too
    if not checksum_valid and (ela_score >= 30 or noise_score >= 30):
        boost += 6.0   # Invalid number + forensic suspicion
    if cross_score >= 80:
        boost += 18.0  # Near-identical front/back
    elif cross_score >= 55:
        boost += 8.0

    final_score = float(np.clip(base_score + boost, 0.0, 100.0))

    # --- Floor rules (don't let strong signals be underweighted) ---
    if yolo_tamper:
        final_score = max(final_score, 58.0)
    if ela_score >= 55 or noise_score >= 55:
        final_score = max(final_score, 52.0)
    elif ela_score >= 35 or noise_score >= 35:
        final_score = max(final_score, 35.0)
    if cross_score >= 80:
        final_score = max(final_score, 67.0)
    if not checksum_valid:
        final_score = max(final_score, 30.0)

    final_score = round(final_score, 1)

    if final_score >= 65:
        risk_level = "HIGH"
    elif final_score >= 40:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    breakdown = {
        "ela_score": round(ela_score, 1),
        "noise_score": round(noise_score, 1),
        "exif_score": round(exif_score, 1),
        "yolo_tamper_score": round(yolo_score, 1),
        "cross_side_score": round(cross_score, 1),
        "checksum_score": round(checksum_score, 1),
        "boost_applied": round(boost, 1),
    }

    fraud_indicators = []
    if ela_score > 50:
        fraud_indicators.append(f"ELA risk elevated ({round(ela_score, 1)}/100) — possible image editing")
    if noise_score > 50:
        fraud_indicators.append(f"Noise anomaly detected ({round(noise_score, 1)}/100) — possible region pasting")
    if exif_score > 50:
        for reason in exif_result.get("reasons", []):
            fraud_indicators.append(f"EXIF: {reason}")
    if yolo_tamper:
        fraud_indicators.append(f"YOLO tamper detection confidence: {round(yolo_tamper_confidence * 100)}%")
    if cross_score >= 55:
        fraud_indicators.append(f"Cross-side similarity: {cross_reason}")
    if not checksum_valid:
        fraud_indicators.append("Invalid Aadhaar number — Verhoeff checksum failed")
    if boost >= 12:
        fraud_indicators.append(f"Multiple signals corroborated — boosted score by {round(boost, 1)} points")

    return {
        "final_score": final_score,
        "risk_level": risk_level,
        "fraud_indicators": fraud_indicators,
        "breakdown": breakdown,
        "forensic_decision": _classify_risk(final_score),
    }
