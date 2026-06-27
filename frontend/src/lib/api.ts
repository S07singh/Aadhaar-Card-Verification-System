/**
 * API client — wraps all calls to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalysisResult {
  status: string;
  fraud_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH";
  fraud_indicators: string[];
  score_breakdown: {
    ela_score: number;
    noise_score: number;
    exif_score: number;
    yolo_tamper_score: number;
    qr_mismatch_score: number;
    checksum_score: number;
  };
  ocr_data: {
    name: string;
    aadhaar_number: string;
    gender: string;
    date_of_birth: string;
    address: string;
  };
  qr_data: {
    decoded: boolean;
    qr_type: string;
    name: string;
    dob: string;
    gender: string;
    address: string;
    error?: string;
  };
  qr_mismatches: string[];
  checksum: {
    valid: boolean;
    reason: string;
    number: string;
  };
  yolo: {
    detection_count: number;
    average_confidence: number;
    is_tampered: boolean;
    detections: Array<{
      class_name: string;
      class_id: number;
      bbox: number[];
      confidence: number;
    }>;
    annotated_image: string | null;
  };
  forensics: {
    ela: {
      risk_score: number;
      mean_intensity?: number;
      global_variance?: number;
      block_inconsistency?: number;
      image: string | null;
      error?: string;
    };
    noise: {
      risk_score: number;
      suspicious_region_ratio?: number;
      heatmap: string | null;
      error?: string;
    };
    exif: {
      risk_score: number;
      software_detected?: string;
      camera_make?: string;
      camera_model?: string;
      reasons: string[];
      raw_fields: Record<string, string>;
    };
  };
}

export async function analyzeCard(
  frontImage: File,
  backImage: File,
  onProgress?: (step: string) => void
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("front_image", frontImage);
  formData.append("back_image", backImage);

  onProgress?.("Uploading images...");

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Server error: ${response.status}`);
  }

  onProgress?.("Processing complete");
  return response.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}
