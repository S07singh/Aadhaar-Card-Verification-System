"""
Noise Anomaly Analysis — Detects pixel inconsistencies that indicate copy-paste or editing.
Uses Gaussian blur subtraction to expose unnatural variance patterns.
"""

import os
import cv2
import numpy as np


def run_noise_analysis(image_path: str) -> dict:
    """
    Performs noise residual analysis.
    Saves heatmap + suspicious mask to assets/noise/.
    Returns a risk score and anomaly metrics.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {"risk_score": 30.0, "error": "Could not read image"}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Gaussian blur — approximates "expected" smooth noise floor
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Noise residual = difference between actual and smooth
        noise_residual = cv2.subtract(gray, blurred)

        # Normalize for heatmap
        residual_norm = cv2.normalize(noise_residual, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(residual_norm, cv2.COLORMAP_JET)

        # Threshold for suspicious high-noise regions
        abs_noise = cv2.absdiff(gray, blurred)
        _, suspicious_mask = cv2.threshold(abs_noise, 25, 255, cv2.THRESH_BINARY)

        # Morphological cleanup
        kernel = np.ones((3, 3), np.uint8)
        suspicious_mask = cv2.morphologyEx(suspicious_mask, cv2.MORPH_CLOSE, kernel)

        # Compute anomaly metrics
        noise_array = noise_residual.astype(np.float32) / 255.0
        mean_noise = float(np.mean(noise_array))
        variance_noise = float(np.var(noise_array))
        suspicious_ratio = float(np.sum(suspicious_mask > 0)) / float(suspicious_mask.size)

        # Risk score weighted by suspicious area and variance
        risk_score = min(
            round((variance_noise * 500) + (suspicious_ratio * 80) + (mean_noise * 50), 2),
            100.0
        )

        # Save outputs
        noise_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "noise")
        os.makedirs(noise_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(image_path))[0]
        heatmap_path = os.path.join(noise_dir, f"noise_heatmap_{base}.jpg")
        mask_path = os.path.join(noise_dir, f"noise_mask_{base}.jpg")
        cv2.imwrite(heatmap_path, heatmap)
        cv2.imwrite(mask_path, suspicious_mask)

        return {
            "risk_score": risk_score,
            "mean_noise": round(mean_noise, 6),
            "variance_noise": round(variance_noise, 6),
            "suspicious_region_ratio": round(suspicious_ratio, 4),
            "heatmap_path": heatmap_path,
            "mask_path": mask_path,
        }

    except Exception as e:
        return {"risk_score": 30.0, "error": str(e)}
