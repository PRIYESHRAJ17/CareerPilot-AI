
import { z } from "zod";

export const JobSearchRequestSchema = z.object({
  role: z.string().trim().min(2, "Enter at least 2 characters for the role.").max(120),
  location: z.string().trim().max(120).optional(),
  experience_years: z.number().min(0).max(50),
  minimum_salary_lpa: z.number().min(0).max(500).optional(),
  preferred_work_modes: z.array(z.enum(["remote", "hybrid", "on-site"])).max(3),
  skills: z.array(z.string().trim().min(1).max(80)).max(50),
  target_industries: z.array(z.string().trim().min(1).max(80)).max(20),
});

export const GoalSchema = z.string().trim().min(3).max(2000);

export function normalizeCommaList(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(/[,;\n]+/)
        .map((item) => item.trim().replace(/^[^a-zA-Z0-9#+.]+|[^a-zA-Z0-9#+.]+$/g, ""))
        .filter(Boolean)
        .slice(0, 50),
    ),
  );
}
