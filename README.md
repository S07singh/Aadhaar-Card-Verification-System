<div align="center">

# 🛡️ Aadhaar Card Verification System

**An AI-powered forensic fraud detection system for Aadhaar cards**  
Built with YOLOv8 · PaddleOCR · FastAPI · Next.js

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=flat-square)](https://ultralytics.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📖 Overview

The **Aadhaar Card Verification System** is a full-stack AI application that analyzes Aadhaar card images for signs of forgery and tampering. It runs a **6-layer forensic pipeline** combining computer vision, OCR, and image forensics to produce a fraud risk score from 0–100.

> ⚠️ **Disclaimer**: This system is built for educational and research purposes. It does not connect to UIDAI servers or official databases. Always use official UIDAI channels for legally compliant verification.

---

## ✨ Features

- 🔍 **YOLOv8 Field Detection** — Automatically localizes Name, Aadhaar Number, DOB, Gender, and Address regions on the card
- 📝 **PaddleOCR Extraction** — Bilingual (English + Hindi) text extraction from detected field regions
- 🔐 **Verhoeff Checksum** — Validates the 12-digit Aadhaar number using the official Verhoeff algorithm
- 🧪 **ELA Forensics** — Error Level Analysis detects JPEG re-compression artifacts from image editing
- 🌡️ **Noise Analysis** — Pixel variance heatmap detects inconsistent noise patterns from region pasting
- 📁 **EXIF Metadata Check** — Detects editing software traces (Photoshop, GIMP, etc.) in image metadata
- 🔄 **Cross-Side Similarity** — Compares front and back to catch same-image fraud attempts
- 📊 **Weighted Fraud Score** — All signals combined into a 0–100 score with risk classification

---

## 🏗️ Architecture

```
Aadhaar_Card verification system/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # API routes & pipeline orchestration
│   ├── model/
│   │   └── best.pt             # Trained YOLOv8 model (6.25 MB)
│   ├── pipeline/
│   │   ├── ela_analysis.py     # Error Level Analysis
│   │   ├── noise_analysis.py   # Noise heatmap generation
│   │   ├── exif_analysis.py    # EXIF metadata forensics
│   │   └── forgery_scorer.py   # Weighted fraud score engine
│   ├── services/
│   │   ├── yolo_service.py     # YOLOv8 field detection
│   │   ├── ocr_service.py      # PaddleOCR text extraction
│   │   └── verhoeff.py         # Aadhaar checksum validator
│   └── requirements.txt
│
└── frontend/                   # Next.js 15 frontend
    └── src/
        ├── app/
        │   ├── page.tsx         # Upload page
        │   └── results/
        │       └── page.tsx     # Analysis results dashboard
        └── lib/
            └── api.ts           # API client & TypeScript types
```

---

## 🔬 Detection Pipeline

```
Upload Front + Back Image
        │
        ▼
┌─────────────────────┐
│  1. YOLO Detection  │  ← Locates field regions on front image
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. PaddleOCR       │  ← Extracts text from each field crop
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. Verhoeff Check  │  ← Validates 12-digit Aadhaar number
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│  4. Forensic Analysis (on both sides)   │
│     ├── ELA         (editing artifacts) │
│     ├── Noise       (region pasting)    │
│     └── EXIF        (software traces)   │
└──────────┬───────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  5. Cross-Side      │  ← Compares front vs back similarity
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  6. Fraud Scorer    │  ← Weighted score 0–100 + risk level
└─────────────────────┘
```

---

## 📊 Fraud Score Weights

| Signal | Weight | Description |
|--------|--------|-------------|
| ELA Analysis | 30% | Image compression artifact detection |
| Noise Analysis | 26% | Pixel-level noise inconsistency |
| Cross-Side Similarity | 18% | Front vs back visual comparison |
| YOLO Tamper | 17% | AI-detected tamper regions |
| EXIF Forensics | 9% | Metadata & software fingerprints |

**Risk Classification:**
- 🟢 **Low Risk** (0–39) — Likely authentic
- 🟡 **Moderate Risk** (40–64) — Needs manual review
- 🔴 **High Risk** (65–100) — Likely forged

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### 1. Clone the Repository

```bash
git clone https://github.com/S07singh/Aadhaar-Card-Verification-System.git
cd Aadhaar-Card-Verification-System
```

### 2. Backend Setup

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> 📝 **First Run**: PaddleOCR will auto-download model weights (~300MB). This only happens once.

Backend API available at: **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### 3. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend available at: **http://localhost:3000**

### 4. Model File

Ensure your trained YOLOv8 model is placed at:
```
backend/model/best.pt
```

The model was trained to detect 5 classes:
| Class ID | Field |
|----------|-------|
| 0 | `aadhaar_number` |
| 1 | `dob` |
| 2 | `gender` |
| 3 | `name` |
| 4 | `address` |

---

## 🖥️ Usage

1. Open **http://localhost:3000** in your browser
2. Upload the **front side** of the Aadhaar card
3. Upload the **back side** of the Aadhaar card
4. Click **"Start Fraud Analysis"**
5. View the detailed results dashboard with:
   - Fraud score gauge (0–100)
   - OCR extracted fields (Name, Aadhaar Number, DOB, Gender)
   - Verhoeff checksum result
   - YOLO detection visualization
   - ELA & Noise forensic heatmaps
   - EXIF metadata findings
   - Cross-side similarity check

---

## 🛠️ Tech Stack

### Backend
| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.0 | REST API framework |
| Uvicorn | 0.30.6 | ASGI server |
| Ultralytics | 8.2.80 | YOLOv8 object detection |
| PaddleOCR | 2.9.1 | Bilingual OCR engine |
| PaddlePaddle | 3.0.0 | Deep learning framework |
| OpenCV | 4.10.0 | Image processing |
| Pillow | 10.4.0 | Image I/O & EXIF |
| scikit-image | 0.24.0 | ELA & noise analysis |
| NumPy | 1.26.4 | Numerical operations |

### Frontend
| Package | Purpose |
|---------|---------|
| Next.js 15 | React framework with SSR |
| TypeScript | Type-safe development |
| Tailwind CSS | Utility-first styling |

---

## 🧩 API Reference

### `POST /api/analyze`

Runs the full fraud detection pipeline.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `front_image` | File | Front side of Aadhaar card |
| `back_image` | File | Back side of Aadhaar card |

**Response:**
```json
{
  "status": "success",
  "fraud_score": 23.5,
  "risk_level": "LOW",
  "forensic_decision": "Likely Authentic",
  "fraud_indicators": [],
  "ocr_data": {
    "name": "Sudhir Kumar Singh",
    "aadhaar_number": "853909925522",
    "date_of_birth": "10/04/2005",
    "gender": "MALE",
    "address": "..."
  },
  "checksum": {
    "valid": true,
    "reason": "Valid Aadhaar (checksum passed)",
    "number": "853909925522"
  },
  "score_breakdown": {
    "ela_score": 0.4,
    "noise_score": 2.7,
    "exif_score": 50.0,
    "yolo_tamper_score": 6.0,
    "checksum_score": 0.0
  }
}
```

### `GET /api/health`

```json
{ "status": "ok", "service": "Aadhaar Verification API" }
```

---

## 📁 Model Training

The YOLOv8 object detection model was trained using the notebook:

```text
Aadhaar_YOLOv8_Training.ipynb
```

### Dataset

The model was trained on the **Aadhar Card Entity Detection** dataset provided by **Roboflow Universe**.

- **Dataset:** https://universe.roboflow.com/jizo/aadhar-card-entity-detection/dataset/1
- **Platform:** Roboflow Universe
- **Task:** Object Detection
- **Model:** YOLOv8

The dataset contains annotated Aadhaar card images with bounding boxes for important fields such as:

| Class |
|--------|
| Aadhaar Number |
| Name |
| Date of Birth |
| Gender |
| Address |

Training was performed using **Ultralytics YOLOv8**, and the exported weights are stored as:

```text
backend/model/best.pt
```

> The original dataset is excluded from this repository due to its size and Roboflow licensing. Please download it directly from Roboflow Universe if you wish to retrain the model.

---

## ⚙️ Configuration

### Environment Variables

Create `backend/.env` for custom configuration:
```env
# Backend
HOST=0.0.0.0
PORT=8000
```

Create `frontend/.env.local` to point to a custom backend:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `PaddleOCR download error` | Wait for auto-download (~300MB) on first run |
| `YOLO model not found` | Ensure `backend/model/best.pt` exists |
| `CORS error in browser` | Ensure backend is running on port 8000 |
| `ccache warning from Paddle` | Harmless — safely ignore it |
| `Fields detected in wrong positions` | Check CLASS_NAMES in `yolo_service.py` match your model |

---

## 📚 Dataset Citation

If you use this project or retrain the model, please credit the original dataset creators.

**Dataset:**
Aadhar Card Entity Detection Dataset

**Source:**
https://universe.roboflow.com/jizo/aadhar-card-entity-detection/dataset/1

**Platform:**
Roboflow Universe

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — Object detection framework
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — OCR engine
- [UIDAI](https://uidai.gov.in) — Aadhaar specification & Verhoeff checksum documentation
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [Roboflow Universe – Aadhar Card Entity Detection Dataset](https://universe.roboflow.com/jizo/aadhar-card-entity-detection/dataset/1) — Dataset used for training the YOLOv8 field detection model.

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/S07singh">S07singh</a></sub>
</div>
