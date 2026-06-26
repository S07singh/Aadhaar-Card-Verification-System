"""
YOLO Service — Runs the trained YOLOv8 model on Aadhaar card images.
Detects 5 field regions: NAME, AADHAR_NUMBER, GENDER, DATE_OF_BIRTH, ADDRESS
and also checks for tampered regions (class IDs >= threshold).
"""

import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image

# Class ID → Field name mapping (must match the trained model's data.yaml)
# Verified from model: {0: 'aadhaar_number', 1: 'dob', 2: 'gender', 3: 'name', 4: 'address'}
CLASS_NAMES = {
    0: "AADHAR_NUMBER",
    1: "DATE_OF_BIRTH",
    2: "GENDER",
    3: "NAME",
    4: "ADDRESS",
}

_model: YOLO | None = None


def get_model() -> YOLO:
    """Lazy-load the YOLO model (only once per process)."""
    global _model
    if _model is None:
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "model", "best.pt"
        )
        model_path = os.path.abspath(model_path)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")
        _model = YOLO(model_path)
        print(f"[YOLO] Loaded model from {model_path}")
        print(f"[YOLO] Classes: {_model.names}")
    return _model


def run_yolo_detection(image_path: str, conf_threshold: float = 0.25) -> dict:
    """
    Run YOLOv8 on an Aadhaar card image.

    Returns:
        detections: list of {class_name, bbox [x1,y1,x2,y2], confidence}
        annotated_image_path: path to the saved annotated image
        is_tampered: True if any tampered class detected
        average_confidence: float
    """
    try:
        model = get_model()
        results = model.predict(image_path, conf=conf_threshold, verbose=False)[0]

        detections = []
        confidences = []
        is_tampered = False

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            class_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")

            # If the model was trained with 'Tampered' as a class name
            if class_name.lower() == "tampered":
                is_tampered = True

            detections.append({
                "class_name": class_name,
                "class_id": cls_id,
                "bbox": [x1, y1, x2, y2],
                "confidence": round(conf, 4),
            })
            confidences.append(conf)

        # Save annotated image
        annotated = results.plot()
        annotated_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "annotated")
        os.makedirs(annotated_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(image_path))[0]
        annotated_path = os.path.join(annotated_dir, f"annotated_{base}.jpg")
        cv2.imwrite(annotated_path, annotated)

        return {
            "detections": detections,
            "annotated_image_path": annotated_path,
            "is_tampered": is_tampered,
            "average_confidence": round(float(np.mean(confidences)) if confidences else 0.0, 4),
            "detection_count": len(detections),
        }

    except Exception as e:
        return {
            "detections": [],
            "annotated_image_path": None,
            "is_tampered": False,
            "average_confidence": 0.0,
            "detection_count": 0,
            "error": str(e),
        }


def crop_field_regions(image_path: str, detections: list[dict]) -> dict[str, np.ndarray]:
    """
    Given YOLO detections, crop each field region from the image.
    Returns a dict: {field_name: cropped_image_array}
    """
    image = cv2.imread(image_path)
    if image is None:
        return {}

    crops = {}
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        # Add small padding
        pad = 4
        y1 = max(0, y1 - pad)
        x1 = max(0, x1 - pad)
        y2 = min(image.shape[0], y2 + pad)
        x2 = min(image.shape[1], x2 + pad)
        crop = image[y1:y2, x1:x2]
        if crop.size > 0:
            field = det["class_name"]
            # If a field appears multiple times, keep highest confidence crop
            if field not in crops:
                crops[field] = crop
    return crops
