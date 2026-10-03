import { z } from "zod";

export const SourceRecordSchema = z.object({
  source: z.string(), source_job_id: z.string(), company: z.string().default(""), title: z.string().default(""),
  location: z.array(z.string()).default([]), remote: z.boolean().default(false),
  employment_type: z.string().nullable().optional(), apply_url: z.string().default(""), source_url: z.string().default(""),
  salary_min_lpa: z.number().nullable().optional(), salary_max_lpa: z.number().nullable().optional(),
  salary_currency: z.string().default("INR"), salary_status: z.string().default("UNDISCLOSED"), salary_confidence: z.number().default(0),
  salary_evidence: z.string().nullable().optional(), posted_at: z.string().nullable().optional(),
}).passthrough();

export const JobResultSchema = z.object({
  source: z.string(), source_job_id: z.string(), sources: z.array(z.string()).default([]), source_count: z.number().default(1),
  source_records: z.array(SourceRecordSchema).default([]), company: z.string().default(""), title: z.string().default(""), location: z.array(z.string()).default([]),
  remote: z.boolean().default(false), employment_type: z.string().nullable().optional(), match_score: z.number().nullable().optional(), decision: z.string().nullable().optional(),
  confidence: z.number().nullable().optional(), strengths: z.array(z.string()).default([]), skill_gaps: z.array(z.string()).default([]), matched_skills: z.array(z.string()).default([]),
  explanation: z.string().default(""), match_breakdown: z.record(z.string(), z.unknown()).nullable().optional(), salary_min_lpa: z.number().nullable().optional(),
  salary_max_lpa: z.number().nullable().optional(), salary_disclosed: z.boolean().default(false), salary_status: z.string().default("UNDISCLOSED"), salary_confidence: z.number().default(0),
  salary_evidence: z.string().nullable().optional(), apply_url: z.string().default(""),
}).passthrough();

export const JobSearchResponseSchema = z.object({
  query: z.string().default(""), location: z.string().nullable().optional(), result_count: z.number().default(0), results: z.array(JobResultSchema).default([]),
  salary_summary: z.record(z.string(), z.unknown()).default({}), source_summary: z.record(z.string(), z.unknown()).default({}),
  candidate_intelligence: z.record(z.string(), z.unknown()).nullable().optional(), career_strategy: z.record(z.string(), z.unknown()).nullable().optional(),
}).passthrough();

export const ResumeAnalysisResponseSchema = z.object({
  filename: z.string().default(""), page_count: z.number().default(0), resume: z.record(z.string(), z.unknown()), intelligence: z.record(z.string(), z.unknown()),
}).passthrough();

export const JobResumeAnalysisResponseSchema = z.record(z.string(), z.unknown());
