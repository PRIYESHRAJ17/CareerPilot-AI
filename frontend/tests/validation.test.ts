import { describe, expect, it } from "vitest";
import { GoalSchema, JobSearchRequestSchema, normalizeCommaList } from "../lib/validation";
describe("validation", () => {
  it("normalizes skills deterministically", () => expect(normalizeCommaList("Python,, React; Python")).toEqual(["Python","React"]));
  it("enforces role and salary boundaries", () => {
    expect(JobSearchRequestSchema.safeParse({role:"A",experience_years:0,preferred_work_modes:[],skills:[],target_industries:[]}).success).toBe(false);
    expect(JobSearchRequestSchema.safeParse({role:"AI Engineer",experience_years:0,minimum_salary_lpa:501,preferred_work_modes:[],skills:[],target_industries:[]}).success).toBe(false);
  });
  it("limits goals", () => expect(GoalSchema.safeParse("x".repeat(2001)).success).toBe(false));
});
