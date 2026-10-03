import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { WebVitals } from "@/components/WebVitals";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport = { width: "device-width", initialScale: 1, maximumScale: 1 } as const;

export const metadata: Metadata = {
  title: {
    default: "CareerPilot AI — Autonomous Career Operating System",
    template: "%s | CareerPilot AI",
  },
  description:
    "AI-orchestrated career intelligence platform combining autonomous agent workflows, deterministic validation, resume ATS parsing, and multi-source opportunity aggregation.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <a href="#main-content" className="skip-link">Skip to content</a>
        <WebVitals />
        {children}
      </body>
    </html>
  );
}
