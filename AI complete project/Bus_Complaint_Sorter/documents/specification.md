# Specification: Bus Complaint Sorter

## 1. Project Overview & Institutional Context
- **Project Name:** Bus Complaint Sorter
- **Institution:** Coimbatore Institute of Technology (CIT)
- **Programme:** AI-Native Engineering Programme – Semester 1
- **Domain:** Campus Transport Operations & Fleet Safety

## 2. Problem Statement
The CIT Transport Department operates 12 dedicated college bus routes serving hundreds of students daily across Coimbatore and surrounding regions. Daily manual triage of heterogeneous student feedback—ranging from critical safety hazards (rash driving, footboard travel, brake failures) to routine delays and route expansion queries—is slow and prone to oversight. An automated, resilient triage system is required to parse, categorize, identify safety emergencies, and present actionable intelligence to transport officers.

## 3. Core Architectural Boundaries & Governance Rules
1. **Human-in-the-Loop Supremacy:** The AI system acts exclusively as a triage assistant. All disciplinary, operational, and driver accountability decisions remain the sole jurisdiction of the Human Transport Officer.
2. **Zero Automated Driver Contact:** The software never contacts or messages bus drivers under any circumstances.
3. **No Automated Fault Attribution:** The system classifies factual hazard categories but never assigns legal or personal fault.
4. **Deterministic Validation Gatekeeper:** LLM outputs are treated as untrusted suggestions and undergo strict deterministic validation (`is_valid()`) before downstream consumption.

## 4. Technical Architecture & Component Flow
- **Data Ingestion:** Reads structured route references (`routes.csv`, 12 routes) and unstructured student complaints (`complaints.csv`, 27 records including Tamil/Tanglish, vague, and urgent reports).
- **Classification Engine (`classify`):**
  - Sends individual complaints to Gemini API with structured system prompt instructions.
  - Generates JSON response: `{"category": str, "urgent": bool, "route": int|null, "summary": str}`.
  - Implements automatic retry logic on JSON formatting anomalies.
  - Provides a deterministic rule-based fallback mode if API or network is unavailable, ensuring 100% crash immunity.
- **Validation Engine (`is_valid`):**
  - Confirms category belongs to: `delay`, `crowding`, `driver`, `vehicle`, `route_request`, `other`.
  - Enforces boolean typing on urgency.
  - Cross-references route numbers against both `routes.csv` and the original complaint text. Hallucinated or non-existent routes are immediately discarded (`null`).
  - Limits summaries to 12 words and strips personally identifiable references.
- **Pure Python Analytics & Reporting (`write_reports`):**
  - `outputs/results.csv`: Complete sorted ledger of all complaints.
  - `outputs/urgent.csv`: Isolated priority escalation list for immediate safety interventions.
  - `outputs/summary.txt`: Executive statistical briefing featuring complaint frequencies, route rankings (highest to lowest), and safety alerts.

## 5. Security & Red-Team Resilience
The application passes adversarial testing against prompt injections, missing route hallucinations, and out-of-bounds route manipulation attacks, maintaining complete schema compliance.
