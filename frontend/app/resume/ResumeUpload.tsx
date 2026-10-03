"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { UploadCloud, FileText, X, CheckCircle2 } from "lucide-react";
import { MAX_RESUME_BYTES } from "@/lib/config";
import { formatFileSize } from "@/lib/formatters";

export function ResumeUpload({
  file,
  onSelect,
  onError,
}: {
  file: File | null;
  onSelect: (file: File | null) => void;
  onError: (message: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function validateAndSelect(selectedFile: File) {
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      if (inputRef.current) inputRef.current.value = "";
      onError("Please upload a PDF resume.");
      return false;
    }

    if (selectedFile.size > MAX_RESUME_BYTES) {
      if (inputRef.current) inputRef.current.value = "";
      onError("The PDF must be smaller than 10 MB.");
      return false;
    }

    onError("");
    onSelect(selectedFile);
    return true;
  }

  function handle(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (!selected) return;

    if (selected.type !== "application/pdf" && !selected.name.toLowerCase().endsWith(".pdf")) {
      event.target.value = "";
      onError("Please upload a PDF resume.");
      return;
    }

    if (selected.size > MAX_RESUME_BYTES) {
      event.target.value = "";
      onError("The PDF must be smaller than 10 MB.");
      return;
    }

    onSelect(selected);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);

    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) {
      validateAndSelect(droppedFile);
    }
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
  }

  function clearFile() {
    if (inputRef.current) {
      inputRef.current.value = "";
    }
    onSelect(null);
    onError("");
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-white/60">
            Resume Upload
          </div>
          <p className="mt-1 text-xs text-white/60">
            Upload your master resume in PDF format (up to 10 MB).
          </p>
        </div>

        {file && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
            <CheckCircle2 size={12} />
            Loaded
          </span>
        )}
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`mt-4 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition ${
          isDragging
            ? "border-cyan-400 bg-cyan-500/[0.05]"
            : "border-white/10 bg-black/10 hover:border-white/20 hover:bg-white/[0.02]"
        }`}
      >
        <UploadCloud
          size={32}
          className={`mb-2 transition ${isDragging ? "text-cyan-400" : "text-white/40"}`}
        />

        <p className="text-sm font-medium text-white/80">
          Drag and drop your PDF here, or{" "}
          <label
            htmlFor="resume-file-input"
            className="cursor-pointer text-cyan-400 underline underline-offset-4 hover:text-cyan-300"
          >
            browse files
          </label>
        </p>

        <p className="mt-1 text-xs text-white/50">
          PDF format only • Maximum file size 10 MB
        </p>

        <input
          id="resume-file-input"
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handle}
          className="sr-only"
        />
      </div>

      {file && (
        <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs">
          <div className="flex items-center gap-2.5 min-w-0">
            <FileText size={18} className="shrink-0 text-cyan-400" />
            <div className="min-w-0">
              <div className="truncate font-medium text-white/90">{file.name}</div>
              <div className="text-[11px] text-white/50">{formatFileSize(file.size)}</div>
            </div>
          </div>

          <button
            type="button"
            onClick={clearFile}
            aria-label="Remove selected resume file"
            className="ml-3 inline-flex items-center gap-1 rounded-lg border border-white/10 px-2.5 py-1 text-[11px] text-white/60 transition hover:bg-white/10 hover:text-white"
          >
            <X size={12} />
            Remove
          </button>
        </div>
      )}
    </div>
  );
}
