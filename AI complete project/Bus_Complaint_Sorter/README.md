# Bus Complaint Sorter – CIT Capstone Project

**Institution:** Coimbatore Institute of Technology (CIT)  
**Programme:** AI-Native Engineering Programme – Semester 1  
**Domain:** Campus Transport & Safety Operations  
**Language:** Python 3.12+

---

## 1. Project Overview
The CIT Bus Complaint Sorter is a reliable, console-based AI application that categorizes student complaints across 12 college bus routes. It leverages Google Gemini API (with deterministic fallback support) to parse messy, multi-lingual, and colloquial complaints (including Tamil/Tanglish), isolate genuine safety emergencies, validate route numbers against an institutional database, and output structured operational intelligence for the CIT Transport Officer.

### Key Governance Principles
- **Human Authority:** The Human Transport Officer makes all final operational decisions.
- **Zero Driver Contact:** The system never contacts or messages bus drivers automatically.
- **No Fault Assignment:** The system classifies factual hazard categories and never decides blame or liability.
- **Never-Crash Architecture:** Includes automated retry logic and a deterministic fallback classifier ensuring zero pipeline aborts even when offline.

---

## 2. Project Folder Structure

```
Bus_Complaint_Sorter/
│
├── main.py                  # Core application pipeline (5 required functions)
├── eval_harness.py          # 5 standard tests + 3 adversarial red-team tests
├── complaints.csv           # 27 realistic complaints (delay, safety, Tanglish, vague)
├── routes.csv               # 12 official CIT college bus routes
├── system_prompt.txt        # 5-role structured framework prompt
├── requirements.txt         # Package dependencies
├── .env.example             # Template for API credentials
├── .gitignore               # Excludes secrets, venvs, and bytecode
├── README.md                # Comprehensive documentation and run guide
│
├── outputs/                 # Auto-generated report directory
│   ├── results.csv          # Categorized ledger of all complaints
│   ├── urgent.csv           # Priority safety action list for Transport Officer
│   └── summary.txt          # Pure-Python statistical ranking and metrics
│
└── documents/               # CIT Capstone Submission Portfolio
    ├── specification.md     # 1-page technical project specification
    ├── judgment_framework.md # Responsibility, auditability, and governance matrix
    ├── cost_latency.md      # API calls, token counts, cost & latency breakdown
    ├── AI_decision_journal.md# Architecture decisions, tradeoffs, and design pivots
    └── reflection.md        # 400-word engineering reflection
```

---

## 3. Five Core Functions in `main.py`

1. `load_complaints()`: Reads `complaints.csv` and returns cleaned complaint records.
2. `load_routes()`: Reads `routes.csv` and returns route-to-area mappings.
3. `classify()`: Interacts with Gemini API using `system_prompt.txt`, enforces JSON output, and retries once if response is invalid.
4. `is_valid()`: Deterministically verifies category, boolean urgency, text-verified route existence, and summary length (<= 12 words).
5. `write_reports()`: Aggregates counts, ranks routes from highest to lowest using pure Python, and writes `results.csv`, `urgent.csv`, and `summary.txt`.

---

## 4. Setup and Execution Guide

### Prerequisites
- Python 3.10 or higher installed.

### Step 1: Install Dependencies
Open your terminal inside the project directory:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional for API Mode)
To use live Gemini API calls:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env     # On Linux/macOS
   copy .env.example .env   # On Windows Command Prompt / PowerShell
   ```
2. Open `.env` and insert your Gemini API Key:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   ```
*(Note: If no key is provided, the application runs seamlessly in Rule-Based Fallback Mode with 100% completion.)*

### Step 3: Run the Main Pipeline
```bash
python main.py
```
This processes all complaints in `complaints.csv` and generates reports inside the `outputs/` folder.

### Step 4: Run the Evaluation and Red-Team Harness
```bash
python eval_harness.py
```
Executes 5 benchmark tests and 3 adversarial red-team tests (Prompt Injection, Route Hallucination, and Out-of-Bounds Route Manipulation).

---

## 5. Output Files Explained

- **`outputs/results.csv`**: Contains `id,category,urgent,route,summary` for every complaint.
- **`outputs/urgent.csv`**: Contains `id,date,route,area,complaint,summary` for only genuine safety hazards (e.g., rash driving, footboard travel, brake defects, engine smoke).
- **`outputs/summary.txt`**: Detailed statistical report with category breakdowns, pure-Python route complaint rankings (highest to lowest), and safety action lists.
