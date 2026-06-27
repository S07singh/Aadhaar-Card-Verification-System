import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Aadhaar Card Verification System",
  description:
    "AI-powered Aadhaar card fraud detection using YOLOv8, PaddleOCR, and forensic analysis.",
  keywords: ["Aadhaar", "fraud detection", "OCR", "YOLO", "verification"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-[#070B14] text-white antialiased min-h-screen" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
