# AI Decision Journal: Bus Complaint Sorter

## Project: Coimbatore Institute of Technology (CIT) – AI-Native Engineering (Semester 1)

This journal records key architectural decisions, trade-offs, and design pivots made during the engineering of the Bus Complaint Sorter application.

---

### Decision 1: Strict JSON Enforcement vs. Freeform LLM Output
- **Context:** Student complaints can be noisy, emotional, or expressed in vernacular terms (Tanglish). Early LLM prototypes occasionally included conversational preambles ("Here is your classification:") or commentary.
- **Decision:** Implemented `response_mime_type="application/json"` with temperature `0.0` and structured exemplar framing in `system_prompt.txt`. Added a regex stripping cleanup layer for markdown wrappers (````json ... ````).
- **Rationale:** Downstream CSV writers and priority queues require reliable parsing. Zero temperature eliminates creative hallucinations in categorization.

---

### Decision 2: Zero-Trust Post-LLM Validation Layer (`is_valid()`)
- **Context:** LLMs are known to hallucinate route numbers (e.g., inferring route 5 because a bus was near Chromepet, even if the student did not write a route number, or inventing non-existent route numbers like 99).
- **Decision:** Mandated that a route is only accepted if:
  1. The route number exists in `routes.csv` (1–12).
  2. The exact integer appears as a substring within the original complaint text.
  If either condition fails, the route is set to `null` and flagged.
- **Rationale:** Fleet managers cannot dispatch personnel based on AI guesses. Route verification must be 100% deterministic.

---

### Decision 3: Deterministic Rule-Based Fallback Mode
- **Context:** In college demonstration environments, network outages, expired API keys, or rate limits can cause crashes during live presentations.
- **Decision:** Built a high-accuracy, zero-crash heuristic fallback inside `classify()`. If `GEMINI_API_KEY` is missing or the API endpoint fails after retry, the system transparently shifts to keyword matching without crashing.
- **Rationale:** Industrial software must degrade gracefully. The application guarantees 100% pipeline completion under any network condition.

---

### Decision 4: Pure Python Statistical Ranking over LLM Aggregation
- **Context:** Consideration was given to asking the LLM to summarize route complaint frequencies and produce the ranked list.
- **Decision:** Rejected LLM aggregation in favor of pure Python dictionaries, `sorted()`, and `Counter` logic in `write_reports()`.
- **Rationale:** LLMs are notoriously error-prone when counting tokens and computing quantitative totals across large datasets. Pure Python is mathematically exact, instantaneous, auditable, and costs zero API tokens.

---

### Decision 5: Non-Autonomous Human Decision Boundary
- **Context:** Requirements strictly forbid automatic driver contact or determining liability.
- **Decision:** The application segregates urgent items into `outputs/urgent.csv` marked specifically as `PENDING TRANSPORT OFFICER REVIEW`. No external communication webhooks or automated messaging protocols exist in the codebase.
- **Rationale:** Preserves human safety ethics and institutional liability standards.
