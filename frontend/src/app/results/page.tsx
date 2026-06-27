"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { AnalysisResult } from "@/lib/api";

const RISK_CONFIG = {
  LOW: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    glow: "glow-green",
    gauge: "#10b981",
    icon: "✓",
    label: "Low Risk",
    description: "No significant fraud indicators detected.",
  },
  MODERATE: {
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    glow: "glow-amber",
    gauge: "#f59e0b",
    icon: "⚠",
    label: "Moderate Risk",
    description: "Some suspicious signals detected. Manual review recommended.",
  },
  HIGH: {
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    glow: "glow-red",
    gauge: "#ef4444",
    icon: "✕",
    label: "High Risk",
    description: "Multiple fraud indicators detected. This card may be forged.",
  },
};

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const stored = sessionStorage.getItem("aadhaar_result");
    if (!stored) { router.push("/"); return; }
    const data: AnalysisResult = JSON.parse(stored);
    setResult(data);
    // Animate score
    let current = 0;
    const target = data.fraud_score;
    const step = target / 60;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      setAnimatedScore(Math.round(current));
      if (current >= target) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [router]);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const risk = RISK_CONFIG[result.risk_level];
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between sticky top-0 bg-[#070B14]/80 backdrop-blur-xl z-50">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/")}
            className="w-8 h-8 rounded-lg glass flex items-center justify-center text-white/50 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="font-semibold text-white/90 text-sm">Analysis Results</span>
        </div>
        <div className={`text-xs font-medium px-3 py-1 rounded-full border ${risk.border} ${risk.bg} ${risk.color}`}>
          {risk.icon} {risk.label}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 pt-8 space-y-6">
        {/* Forensic Decision Banner */}
        {result.forensic_decision && (
          <div className={`glass rounded-2xl px-6 py-4 flex items-center gap-4 border ${
            result.forensic_decision === "Likely Forged" ? "border-red-500/30 bg-red-500/5" :
            result.forensic_decision === "Needs Manual Review" ? "border-amber-500/30 bg-amber-500/5" :
            "border-emerald-500/30 bg-emerald-500/5"
          }`}>
            <span className="text-2xl">
              {result.forensic_decision === "Likely Forged" ? "🚨" :
               result.forensic_decision === "Needs Manual Review" ? "⚠️" : "✅"}
            </span>
            <div>
              <p className="text-xs text-white/40 uppercase tracking-widest mb-0.5">Forensic Decision</p>
              <p className={`font-bold text-base ${
                result.forensic_decision === "Likely Forged" ? "text-red-400" :
                result.forensic_decision === "Needs Manual Review" ? "text-amber-400" : "text-emerald-400"
              }`}>{result.forensic_decision}</p>
            </div>
          </div>
        )}

        {/* Top Row: Score + OCR */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Fraud Score Gauge */}
          <div className={`glass rounded-2xl p-6 flex flex-col items-center justify-center ${risk.glow}`}>
            <p className="text-xs text-white/40 uppercase tracking-widest mb-4">Fraud Score</p>
            <div className="relative w-36 h-36">
              <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                <circle cx="60" cy="60" r="54" className="gauge-track" strokeWidth="10" stroke="rgba(255,255,255,0.06)" fill="none" />
                <circle
                  cx="60" cy="60" r="54"
                  className="gauge-fill"
                  strokeWidth="10"
                  stroke={risk.gauge}
                  fill="none"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-4xl font-bold ${risk.color}`}>{animatedScore}</span>
                <span className="text-white/30 text-xs mt-0.5">/ 100</span>
              </div>
            </div>
            <div className={`mt-4 text-center text-sm font-semibold ${risk.color}`}>{risk.label}</div>
            <p className="text-white/40 text-xs text-center mt-1 max-w-[160px]">{risk.description}</p>
          </div>

          {/* OCR Extracted Data */}
          <div className="md:col-span-2 glass rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-6 h-6 rounded-md bg-indigo-500/20 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-sm font-semibold text-white/80">Extracted Card Data (PaddleOCR)</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Name", value: result.ocr_data.name, icon: "👤" },
                { label: "Aadhaar Number", value: result.ocr_data.aadhaar_number || "—", icon: "🔢" },
                { label: "Date of Birth", value: result.ocr_data.date_of_birth || "—", icon: "📅" },
                { label: "Gender", value: result.ocr_data.gender || "—", icon: "⚧" },
              ].map((field) => (
                <div key={field.label} className="bg-white/3 rounded-xl p-3 border border-white/5">
                  <div className="text-xs text-white/30 mb-1">{field.icon} {field.label}</div>
                  <div className="text-sm font-medium text-white/85 truncate">{field.value || "Not detected"}</div>
                </div>
              ))}
            </div>
            {result.ocr_data.address && (
              <div className="mt-3 bg-white/3 rounded-xl p-3 border border-white/5">
                <div className="text-xs text-white/30 mb-1">📍 Address</div>
                <div className="text-sm text-white/75 leading-relaxed">{result.ocr_data.address}</div>
              </div>
            )}
          </div>
        </div>

        {/* Fraud Indicators */}
        {result.fraud_indicators.length > 0 && (
          <div className="glass rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-red-500/20 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-sm font-semibold text-white/80">Fraud Indicators ({result.fraud_indicators.length})</h2>
            </div>
            <div className="space-y-2">
              {result.fraud_indicators.map((indicator, i) => (
                <div key={i} className="flex items-start gap-3 bg-red-500/5 border border-red-500/15 rounded-xl px-4 py-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                  <p className="text-sm text-red-300/90">{indicator}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Score Breakdown */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white/80 mb-5">Score Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries({
              "ELA Analysis": result.score_breakdown.ela_score,
              "Noise Analysis": result.score_breakdown.noise_score,
              "EXIF Forensics": result.score_breakdown.exif_score,
              "YOLO Tamper": result.score_breakdown.yolo_tamper_score,
              "QR Mismatch": result.score_breakdown.qr_mismatch_score,
              "Checksum": result.score_breakdown.checksum_score,
            }).map(([label, score]) => (
              <ScoreBar key={label} label={label} score={score} />
            ))}
          </div>
        </div>

        {/* Forensic Images Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Annotated Card */}
          <ForensicImageCard
            title="YOLO Detection"
            subtitle={`${result.yolo.detection_count} regions · ${Math.round(result.yolo.average_confidence * 100)}% avg conf`}
            imageSrc={result.yolo.annotated_image}
            badge={result.yolo.is_tampered ? { label: "TAMPERED", color: "text-red-400 bg-red-500/10 border-red-500/30" } : null}
            icon="🔍"
          />
          {/* ELA Front */}
          <ForensicImageCard
            title="ELA — Front"
            subtitle={`Front risk: ${result.forensics.ela.front.risk_score.toFixed(1)} · Back risk: ${result.forensics.ela.back.risk_score.toFixed(1)} · Avg: ${result.forensics.ela.risk_score}`}
            imageSrc={result.forensics.ela.front.image}
            icon="🧪"
          />
          {/* Noise Heatmap */}
          <ForensicImageCard
            title="Noise Heatmap — Front"
            subtitle={`Front risk: ${result.forensics.noise.front.risk_score.toFixed(1)} · Back risk: ${result.forensics.noise.back.risk_score.toFixed(1)}`}
            imageSrc={result.forensics.noise.front.heatmap}
            icon="🌡️"
          />
        </div>

        {/* QR + Checksum + EXIF Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* QR Data */}
          <div className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-base">📷</span>
              <h3 className="text-sm font-semibold text-white/80">QR Code</h3>
              <div className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${result.qr_data.decoded ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" : "text-red-400 bg-red-500/10 border-red-500/30"}`}>
                {result.qr_data.decoded ? "Decoded" : "Failed"}
              </div>
            </div>
            {result.qr_data.decoded ? (
              <div className="space-y-2 text-sm">
                {result.qr_data.name && <QrField label="Name" value={result.qr_data.name} mismatch={result.qr_mismatches.includes("Name")} />}
                {result.qr_data.dob && <QrField label="DOB" value={result.qr_data.dob} mismatch={result.qr_mismatches.includes("Date of Birth")} />}
                {result.qr_data.gender && <QrField label="Gender" value={result.qr_data.gender} mismatch={result.qr_mismatches.includes("Gender")} />}
              </div>
            ) : (
              <p className="text-xs text-white/30 italic">{result.qr_data.error || "QR code not found or unreadable"}</p>
            )}
          </div>

          {/* Checksum */}
          <div className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-base">🔐</span>
              <h3 className="text-sm font-semibold text-white/80">Verhoeff Checksum</h3>
            </div>
            <div className={`text-center py-6 rounded-xl border ${result.checksum.valid ? "bg-emerald-500/5 border-emerald-500/20" : "bg-red-500/5 border-red-500/20"}`}>
              <div className={`text-3xl font-bold mb-2 ${result.checksum.valid ? "text-emerald-400" : "text-red-400"}`}>
                {result.checksum.valid ? "✓" : "✕"}
              </div>
              <div className={`text-sm font-medium ${result.checksum.valid ? "text-emerald-400" : "text-red-400"}`}>
                {result.checksum.valid ? "Valid" : "Invalid"}
              </div>
              <div className="text-xs text-white/30 mt-1">{result.checksum.reason}</div>
              {result.checksum.number && (
                <div className="mt-3 font-mono text-xs text-white/50 tracking-widest">
                  {result.checksum.number.replace(/(\d{4})/g, "$1 ").trim()}
                </div>
              )}
            </div>
          </div>

          {/* EXIF */}
          <div className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-base">📁</span>
              <h3 className="text-sm font-semibold text-white/80">EXIF Metadata</h3>
              <div className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${result.forensics.exif.risk_score > 50 ? "text-red-400 bg-red-500/10 border-red-500/30" : "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"}`}>
                Risk: {result.forensics.exif.risk_score}
              </div>
            </div>
            <div className="space-y-2 text-sm">
              {result.forensics.exif.software_detected && (
                <div className="flex items-center gap-2 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
                  <span className="text-red-400">⚠</span>
                  <span className="text-xs text-red-300">Software: {result.forensics.exif.software_detected}</span>
                </div>
              )}
              {result.forensics.exif.camera_make && (
                <div className="bg-white/3 rounded-lg px-3 py-2">
                  <span className="text-xs text-white/30">Camera: </span>
                  <span className="text-xs text-white/70">{result.forensics.exif.camera_make} {result.forensics.exif.camera_model}</span>
                </div>
              )}
              {result.forensics.exif.reasons.slice(0, 3).map((r, i) => (
                <div key={i} className="text-xs text-white/40 px-2">{r}</div>
              ))}
            </div>
          </div>

          {/* Cross-Side Similarity */}
          <div className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-base">🔄</span>
              <h3 className="text-sm font-semibold text-white/80">Cross-Side Check</h3>
              <div className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${
                result.forensics.cross_side.risk_score >= 55 ? "text-red-400 bg-red-500/10 border-red-500/30" : "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
              }`}>
                Risk: {result.forensics.cross_side.risk_score}
              </div>
            </div>
            <div className={`rounded-xl p-4 border text-center ${
              result.forensics.cross_side.risk_score >= 55
                ? "bg-red-500/5 border-red-500/20"
                : "bg-emerald-500/5 border-emerald-500/20"
            }`}>
              <div className={`text-2xl font-bold mb-1 ${
                result.forensics.cross_side.risk_score >= 55 ? "text-red-400" : "text-emerald-400"
              }`}>
                {result.forensics.cross_side.risk_score >= 80 ? "🚨" :
                 result.forensics.cross_side.risk_score >= 55 ? "⚠️" : "✅"}
              </div>
              <p className="text-xs text-white/50 leading-relaxed">{result.forensics.cross_side.reason || "Front and back look different (expected)"}</p>
              {result.forensics.cross_side.correlation !== undefined && (
                <p className="text-xs text-white/30 mt-2">Correlation: {result.forensics.cross_side.correlation.toFixed(3)}</p>
              )}
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="flex justify-center pt-4">
          <button
            onClick={() => { sessionStorage.removeItem("aadhaar_result"); router.push("/"); }}
            className="glass border border-white/10 text-white/60 hover:text-white hover:border-white/20 transition-all rounded-xl px-8 py-3 text-sm font-medium"
          >
            ← Analyze Another Card
          </button>
        </div>
      </main>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score >= 65 ? "#ef4444" : score >= 35 ? "#f59e0b" : "#10b981";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-white/50">{label}</span>
        <span style={{ color }}>{score.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function QrField({ label, value, mismatch }: { label: string; value: string; mismatch: boolean }) {
  return (
    <div className={`flex justify-between items-center rounded-lg px-3 py-2 ${mismatch ? "bg-red-500/5 border border-red-500/20" : "bg-white/3"}`}>
      <span className="text-xs text-white/40">{label}</span>
      <span className={`text-xs font-medium ${mismatch ? "text-red-400" : "text-white/75"}`}>
        {mismatch ? "⚠ " : ""}{value}
      </span>
    </div>
  );
}

function ForensicImageCard({ title, subtitle, imageSrc, badge, icon }: {
  title: string;
  subtitle: string;
  imageSrc: string | null;
  badge?: { label: string; color: string } | null;
  icon: string;
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm">{icon}</span>
          <h3 className="text-sm font-semibold text-white/80">{title}</h3>
        </div>
        {badge && (
          <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${badge.color}`}>
            {badge.label}
          </span>
        )}
      </div>
      <p className="text-xs text-white/30 mb-3">{subtitle}</p>
      {imageSrc ? (
        <img
          src={imageSrc}
          alt={title}
          className="w-full rounded-xl object-contain max-h-48 bg-black/20"
        />
      ) : (
        <div className="w-full h-32 rounded-xl bg-white/3 border border-white/5 flex items-center justify-center">
          <span className="text-white/20 text-sm">No image available</span>
        </div>
      )}
    </div>
  );
}
