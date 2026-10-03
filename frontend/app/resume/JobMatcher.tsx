"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Sparkles, X, CheckCircle, ArrowRight } from "lucide-react";
import {
  analyzeResumeForJob,
  type ResumeJobAnalysisResponse,
} from "@/lib/api";

const SAMPLE_JD = `Role: Senior Backend Engineer
Requirements:
- 5+ years building distributed backend services in Python, Go, or TypeScript
- Strong knowledge of PostgreSQL, Redis, and modern message brokers (Kafka/RabbitMQ)
- Experience designing RESTful and GraphQL APIs for scale
- Demonstrated production experience with Docker, Kubernetes, and AWS/GCP
- Passion for system reliability, automated testing, and CI/CD pipelines`;

export function JobMatcher({
  file,
  result,
  onResult,
  onError,
}: {
  file: File | null;
  result: ResumeJobAnalysisResponse | null;
  onResult: (result: ResumeJobAnalysisResponse) => void;
  onError: (message: string) => void;
}) {
  const searchParams = useSearchParams();
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handle = window.requestAnimationFrame(() => {
      // Check search params or session storage for handed-off job details
      const jdParam = searchParams?.get("jd");
      const roleParam = searchParams?.get("role");
      const companyParam = searchParams?.get("company");

      if (jdParam) {
        setDescription(decodeURIComponent(jdParam));
      } else if (typeof window !== "undefined") {
        const storedJd = window.sessionStorage.getItem("careerpilot.target_jd");
        if (storedJd) {
          setDescription(storedJd);
        } else if (roleParam || companyParam) {
          setDescription(`Target Position: ${roleParam || "Software Engineer"}\nCompany: ${companyParam || "Tech Company"}\n\nKey Responsibilities and Requirements:\n- Relevant software engineering and backend systems experience.\n- Domain expertise aligned with company technical stack.`);
        }
      }
    });

    return () => window.cancelAnimationFrame(handle);
  }, [searchParams]);

  async function analyze() {
    if (!file) {
      onError("Please choose a resume first.");
      return;
    }

    if (!description.trim()) {
      onError("Please paste a job description first.");
      return;
    }

    setLoading(true);

    try {
      const response = await analyzeResumeForJob(file, description.trim());
      onResult(response);
      onError("");
    } catch (caught) {
      onError(
        caught instanceof Error
          ? caught.message
          : "Unable to analyze the resume for this job.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handlePasteSample() {
    setDescription(SAMPLE_JD);
    onError("");
  }

  function handleClear() {
    setDescription("");
    onError("");
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("careerpilot.target_jd");
    }
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/60">
            <Sparkles size={14} className="text-cyan-400" />
            Job Description Matcher
          </div>
          <p className="mt-1 text-xs text-white/60">
            Evaluate your resume against specific target job requirements to generate tailored ATS scores.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!description && (
            <button
              type="button"
              onClick={handlePasteSample}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/70 transition hover:bg-white/10 hover:text-white"
            >
              Paste Sample JD
            </button>
          )}

          {description && (
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex items-center gap-1 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/60 transition hover:bg-white/10 hover:text-white"
            >
              <X size={12} />
              Clear
            </button>
          )}
        </div>
      </div>

      <label htmlFor="target-job-description" className="mt-4 block text-xs uppercase tracking-[0.18em] text-white/60">
        Target Job Description
      </label>

      <textarea
        id="target-job-description"
        value={description}
        maxLength={12000}
        rows={6}
        onChange={(event) => {
          setDescription(event.target.value);
          onError("");
        }}
        placeholder="Paste full job description, qualifications, and role requirements here..."
        className="mt-2 min-h-36 w-full rounded-2xl border border-white/10 bg-black/10 p-4 text-sm leading-6 text-white outline-none transition focus:border-white/30"
      />

      <div className="mt-2 flex items-center justify-between text-xs text-white/50">
        <span>{description.length}/12000 characters</span>
        {!file && <span className="text-amber-300">Upload a resume above to run match analysis</span>}
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          disabled={loading || !file || !description.trim()}
          onClick={() => void analyze()}
          className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90 disabled:opacity-40"
        >
          {loading ? (
            <>
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
              <span>Analyzing against job...</span>
            </>
          ) : (
            <>
              <span>Analyze against job</span>
              <ArrowRight size={13} />
            </>
          )}
        </button>

        {result && (
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
            <CheckCircle size={14} />
            Analysis synchronized
          </span>
        )}
      </div>

      {result && (
        <div className="mt-6 border-t border-white/10 pt-5">
          <div className="text-xs uppercase tracking-[0.18em] text-white/60">
            Target Match Breakdown
          </div>

          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
              <div className="text-xs text-white/60">Overall Fit Score</div>
              <div className="mt-2 text-3xl font-semibold text-white">
                {Math.round(result.job_resume_analysis.overall_fit_score)}%
              </div>
              <div className="mt-1 text-[11px] text-white/50">Weighted composite match</div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
              <div className="text-xs text-white/60">Evidence Score</div>
              <div className="mt-2 text-3xl font-semibold text-white">
                {Math.round(result.job_resume_analysis.evidence_score)}%
              </div>
              <div className="mt-1 text-[11px] text-white/50">Grounded requirement proofs</div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
              <div className="text-xs text-white/60">Target Role</div>
              <div className="mt-2 truncate text-base font-semibold text-white">
                {result.job_resume_analysis.target_role || "Specified role"}
              </div>
              <div className="mt-1 text-[11px] text-white/50">Parsed role identity</div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
