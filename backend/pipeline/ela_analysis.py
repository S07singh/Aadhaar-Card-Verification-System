"""
ELA (Error Level Analysis) — Detects re-compression artifacts from image editing.
Logic: Re-save at JPEG Q=90, diff with original. High inconsistency = tampering.
"""

import os
import io
import numpy as np
from PIL import Image, ImageChops, ImageEnhance


def run_ela(image_path: str, quality: int = 90, block_size: int = 32) -> dict:
    """
    Runs Error Level Analysis on the given image.
    Returns risk score and statistics. Optionally saves the ELA visualization.
    """
    try:
        original = Image.open(image_path).convert("RGB")

        # Re-save to a buffer at reduced quality
        buffer = io.BytesIO()
        original.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        compressed = Image.open(buffer).convert("RGB")

        # Pixel-level difference
        ela_image = ImageChops.difference(original, compressed)

        # Amplify for visualization
        amplified = ImageEnhance.Brightness(ela_image).enhance(10)

        ela_array = np.array(ela_image).astype("float32") / 255.0

        mean_intensity = float(np.mean(ela_array))
        variance = float(np.var(ela_array))

        # Block-level inconsistency (detects patched regions)
        h, w, _ = ela_array.shape
        block_variances = []
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                block = ela_array[i:i + block_size, j:j + block_size]
                if block.size > 0:
                    block_variances.append(float(np.var(block)))

        block_inconsistency = float(np.std(block_variances)) if block_variances else 0.0

        # Weighted risk score (normalized 0–100)
        raw_risk = (variance * 200) + (mean_intensity * 100) + (block_inconsistency * 300)
        risk_score = min(round(raw_risk, 2), 100.0)

        # Save ELA visualization
        ela_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "ela")
        os.makedirs(ela_dir, exist_ok=True)
        ela_out_path = os.path.join(ela_dir, f"ela_{os.path.basename(image_path)}.jpg")
        amplified.save(ela_out_path, "JPEG")

        return {
            "risk_score": risk_score,
            "mean_intensity": round(mean_intensity, 6),
            "global_variance": round(variance, 6),
            "block_inconsistency": round(block_inconsistency, 6),
            "ela_image_path": ela_out_path,
        }

    except Exception as e:
        return {"risk_score": 35.0, "error": str(e)}
