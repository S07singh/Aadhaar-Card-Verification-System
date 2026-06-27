"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { analyzeCard } from "@/lib/api";

interface CardFile {
  file: File | null;
  preview: string | null;
  name: string;
}

export default function UploadPage() {
  const router = useRouter();
  const [front, setFront] = useState<CardFile>({ file: null, preview: null, name: "" });
  const [back, setBack] = useState<CardFile>({ file: null, preview: null, name: "" });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("");
  const [error, setError] = useState("");
  const [dragFront, setDragFront] = useState(false);
  const [dragBack, setDragBack] = useState(false);
  const frontRef = useRef<HTMLInputElement>(null);
  const backRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File, side: "front" | "back") => {
    const preview = URL.createObjectURL(file);
    if (side === "front") setFront({ file, preview, name: file.name });
    else setBack({ file, preview, name: file.name });
  };

  const onDrop = useCallback((e: React.DragEvent, side: "front" | "back") => {
    e.preventDefault();
    side === "front" ? setDragFront(false) : setDragBack(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) handleFile(file, side);
  }, []);

  const handleAnalyze = async () => {
    if (!front.file || !back.file) {
      setError("Please upload both front and back images.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      setStep("Uploading images to server...");
      const result = await analyzeCard(front.file, back.file, setStep);
      sessionStorage.setItem("aadhaar_result", JSON.stringify(result));
      router.push("/results");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Analysis failed. Please try again.";
      setError(msg);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
            <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <span className="font-semibold text-white/90 text-sm tracking-wide">Aadhaar Verify</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/40">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          AI-Powered Detection
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <div className="text-center mb-14 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-xs text-indigo-300 mb-6">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            7-Layer Fraud Detection
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-4 leading-tight">
            <span className="gradient-text">Aadhaar Card</span>
            <br />
            <span className="text-white/90">Verification System</span>
          </h1>
          <p className="text-white/50 text-lg max-w-xl mx-auto leading-relaxed">
            Upload both sides of your Aadhaar card. Our AI analyzes it through
            YOLO detection, PaddleOCR, QR decoding, and forensic analysis.
          </p>
        </div>

        {/* Upload Grid */}
        <div className="w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
          {/* Front Upload */}
          <UploadZone
            side="front"
            label="Front Side"
            file={front}
            drag={dragFront}
            inputRef={frontRef}
            onDragEnter={() => setDragFront(true)}
            onDragLeave={() => setDragFront(false)}
            onDrop={(e) => onDrop(e, "front")}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f, "front"); }}
            onClick={() => frontRef.current?.click()}
            icon={
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            }
          />
          {/* Back Upload */}
          <UploadZone
            side="back"
            label="Back Side"
            file={back}
            drag={dragBack}
            inputRef={backRef}
            onDragEnter={() => setDragBack(true)}
            onDragLeave={() => setDragBack(false)}
            onDrop={(e) => onDrop(e, "back")}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f, "back"); }}
            onClick={() => backRef.current?.click()}
            icon={
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
            }
          />
        </div>

        {/* Error */}
        {error && (
          <div className="w-full max-w-3xl mb-5 glass border-red-500/30 rounded-xl px-5 py-3 flex items-center gap-3 text-red-400 text-sm">
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {/* Analyze Button */}
        <button
          id="analyze-btn"
          onClick={handleAnalyze}
          disabled={loading || !front.file || !back.file}
          className={`
            relative w-full max-w-3xl h-14 rounded-2xl font-semibold text-base
            transition-all duration-300 overflow-hidden group
            ${front.file && back.file && !loading
              ? "bg-indigo-600 hover:bg-indigo-500 glow-indigo text-white cursor-pointer"
              : "bg-white/5 text-white/30 cursor-not-allowed border border-white/10"
            }
          `}
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span className="text-sm">{step || "Analyzing..."}</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              Start Fraud Analysis
            </div>
          )}
        </button>

        {/* Pipeline Steps */}
        <div className="w-full max-w-3xl mt-10 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: "🔍", label: "YOLO Detection", desc: "Field localization" },
            { icon: "📝", label: "PaddleOCR", desc: "Text extraction" },
            { icon: "📷", label: "QR Decode", desc: "Data verification" },
            { icon: "🧪", label: "Forensics", desc: "ELA + Noise + EXIF" },
          ].map((item) => (
            <div key={item.label} className="glass rounded-xl p-4 text-center">
              <div className="text-2xl mb-2">{item.icon}</div>
              <div className="text-xs font-semibold text-white/80 mb-0.5">{item.label}</div>
              <div className="text-xs text-white/40">{item.desc}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

// ── Upload Zone Component ──────────────────────────────────────────────────────
function UploadZone({
  side, label, file, drag, inputRef, icon,
  onDragEnter, onDragLeave, onDrop, onChange, onClick,
}: {
  side: string;
  label: string;
  file: CardFile;
  drag: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  icon: React.ReactNode;
  onDragEnter: () => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onClick: () => void;
}) {
  return (
    <div
      className={`upload-zone p-6 cursor-pointer transition-all duration-300 ${drag ? "drag-over" : ""}`}
      onClick={onClick}
      onDragOver={(e) => e.preventDefault()}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        id={`upload-${side}`}
        onChange={onChange}
      />
      {file.preview ? (
        <div className="relative">
          <img
            src={file.preview}
            alt={`${label} preview`}
            className="w-full h-40 object-cover rounded-lg"
          />
          <div className="absolute inset-0 rounded-lg bg-gradient-to-t from-black/60 to-transparent flex items-end p-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs text-white/80 truncate">{file.name}</span>
            </div>
          </div>
          <div className="absolute top-2 right-2 glass rounded-md px-2 py-1 text-xs text-white/70">
            {label}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-40 gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {icon}
            </svg>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white/70">{label}</p>
            <p className="text-xs text-white/30 mt-1">Drag & drop or click to upload</p>
          </div>
          <div className="text-xs text-white/20">JPG, PNG, BMP supported</div>
        </div>
      )}
    </div>
  );
}
