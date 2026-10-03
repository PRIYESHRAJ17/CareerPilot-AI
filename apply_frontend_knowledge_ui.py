from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 occurrence, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")

agentic = ROOT / "frontend" / "lib" / "agentic.ts"
page = ROOT / "frontend" / "app" / "page.tsx"

replace_once(
    agentic,
    "export interface AgenticRunResponse {\n",
    """export interface KnowledgeEvidence {
  evidence_id: string;
  source_id: string;
  publisher: string;
  title: string;
  category: string;
  topics: string[];
  url: string;
  resolved_url: string;
  retrieval_method: string;
  relevance: number;
  text: string;
}


export interface AgenticRunResponse {
""",
)

replace_once(
    agentic,
    "  delegation_trace: DelegationTrace[];\n\n",
    "  delegation_trace: DelegationTrace[];\n\n  career_knowledge_evidence: KnowledgeEvidence[];\n\n",
)

replace_once(
    page,
    "  type AgenticRunResponse,\n  type DelegationTrace,\n",
    "  type AgenticRunResponse,\n  type DelegationTrace,\n  type KnowledgeEvidence,\n",
)

anchor = """function getRecommendationAction(
  recommendation: Record<string, unknown>,
): string {
  const action = recommendation.action;

  return typeof action === "string"
    ? action
    : "Review this recommendation.";
}


export default function Home() {
"""
replacement = """function getRecommendationAction(
  recommendation: Record<string, unknown>,
): string {
  const action = recommendation.action;

  return typeof action === "string"
    ? action
    : "Review this recommendation.";
}


function getEvidencePreview(
  evidence: KnowledgeEvidence,
): string {
  const text = evidence.text.trim();

  if (text.length <= 360) {
    return text;
  }

  return `${text.slice(0, 360).trim()}…`;
}


export default function Home() {
"""
replace_once(page, anchor, replacement)

anchor = """              {/* RECOMMENDATIONS */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
"""
section = """              {/* CAREER KNOWLEDGE EVIDENCE */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">

                <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.18em] text-white/30">
                      Career knowledge
                    </div>

                    <h2 className="mt-2 text-2xl font-semibold">
                      Evidence behind the reasoning
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-white/35">
                      Retrieved from CareerPilot's career-intelligence knowledge base and passed into the workflow as supporting evidence.
                    </p>
                  </div>

                  <div className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/50">
                    {result.career_knowledge_evidence?.length ?? 0} sources used
                  </div>
                </div>

                <div className="mt-5 space-y-3">
                  {result.career_knowledge_evidence?.length ? (
                    result.career_knowledge_evidence.map((evidence) => (
                      <article
                        key={evidence.evidence_id}
                        className="rounded-2xl border border-white/8 bg-black/10 p-5"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] text-white/45">
                            {evidence.publisher}
                          </span>

                          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] text-white/35">
                            {evidence.source_id}
                          </span>

                          <span className="ml-auto text-[10px] text-white/30">
                            relevance {evidence.relevance.toFixed(3)}
                          </span>
                        </div>

                        <h3 className="mt-3 font-medium">
                          {evidence.title}
                        </h3>

                        <p className="mt-2 text-sm leading-6 text-white/45">
                          {getEvidencePreview(evidence)}
                        </p>

                        <a
                          href={evidence.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-3 inline-block text-xs text-white/40 underline decoration-white/15 underline-offset-4 transition hover:text-white/70"
                        >
                          View source ↗
                        </a>
                      </article>
                    ))
                  ) : (
                    <div className="rounded-2xl border border-white/8 p-5 text-sm text-white/35">
                      No external career knowledge evidence was retrieved for this run.
                    </div>
                  )}
                </div>

              </section>


              {/* RECOMMENDATIONS */}

              <section className="rounded-3xl border border-white/10 bg-white/[0.025] p-6">
"""
replace_once(page, anchor, section)

anchor = """                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Tools
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.tools_used.length}
                    </div>
                  </div>

                </div>
"""
replacement = """                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Tools
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.tools_used.length}
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/8 bg-black/10 p-3">
                    <div className="text-[9px] uppercase tracking-wider text-white/25">
                      Evidence
                    </div>

                    <div className="mt-1 text-xl font-semibold">
                      {result.career_knowledge_evidence?.length ?? 0}
                    </div>
                  </div>

                </div>
"""
replace_once(page, anchor, replacement)

print("Frontend knowledge evidence UI patch applied.")
