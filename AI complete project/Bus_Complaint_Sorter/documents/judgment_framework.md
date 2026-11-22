# Judgment Framework: Bus Complaint Sorter

## 1. System Responsibility Matrix

The table below delineates the cost of errors, algorithmic verifiability without AI, and final institutional accountability across each pipeline stage:

| Pipeline Component | Cost of Being Wrong | Can It Be Verified Without AI? | Accountable Entity |
| :--- | :--- | :--- | :--- |
| **Classification** (`category`) | **Low to Moderate:** Misclassifying a delay as a vehicle complaint delays operational filing, but does not endanger lives. | **Partially:** Keyword matching can catch common terms, but nuanced natural language (e.g., Tanglish, sarcasm) requires semantic reasoning or human audit. | **Transport Operations Clerk / Transport Officer** |
| **Urgency Detection** (`urgent`) | **Critical / Catastrophic:** A False Negative (missing faulty brakes, rash driving, footboard travel) risks student injury or loss of life. A False Positive creates temporary administrative noise. | **Yes (Deterministically Audited):** A deterministic safety-keyword dictionary can flag critical risks if the AI misses them, ensuring defense-in-depth. | **CIT Transport Officer (Human Decision Maker)** |
| **Route Extraction** (`route`) | **Moderate:** Wrong route attribution routes inspection crews to the wrong bus depot, wasting time and fuel. | **Yes:** Pure Python string search verifies whether the route digit actually exists within the original student complaint text and in `routes.csv`. | **Data Validation Function (`is_valid()`) & Clerk** |
| **Validation Layer** (`is_valid()`) | **High:** Failing to sanitize LLM output can corrupt downstream databases or trigger application crashes midway through processing. | **Yes:** Standard unit test harnesses and strict type/schema validators enforce integrity without AI. | **Software Engineer / System Architect** |
| **Report Generation** (`write_reports`) | **Moderate to High:** Incorrect aggregation or corrupted CSV output distorts administrative resource allocation. | **Yes:** Pure Python sorting, counting, and standard file I/O operations are 100% auditable without AI. | **System Runtime & Python Standard Library** |

---

## 2. Human Authority and Ethical Governance

### Human-in-the-Loop Supremacy
- **No Autonomous Action:** The Bus Complaint Sorter is an assistive prioritization tool, not an autonomous agent. It outputs structured data (`outputs/urgent.csv`) to enable human transport officers to act quickly.
- **The Human Transport Officer makes all final decisions:**
  1. Driver counseling or disciplinary inquiries.
  2. Route diversion, bus replacement, or maintenance scheduling.
  3. Physical inspection of flagged mechanical issues (e.g., tyres, doors, brakes).

### Strict Prohibitions
1. **Never Contact Drivers Automatically:** Under no circumstance does the system broadcast messages, push notifications, or alerts directly to bus drivers. All communications follow official institutional hierarchies.
2. **Never Decide Fault or Responsibility:** The AI system is strictly instructed to classify factual incident categories. It is strictly forbidden from assessing guilt, legal liability, or driver negligence.
