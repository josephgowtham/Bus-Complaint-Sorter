# Cost and Latency Analysis: CIT Bus Complaint Sorter

## 1. Operational Parameters & Workload Estimate
- **Institution:** Coimbatore Institute of Technology (CIT)
- **Fleet Scope:** 12 Bus Routes
- **Daily Volume Estimate:** 50 to 100 student complaints per working day during peak semester periods.
- **Baseline Batch Size for Evaluation:** 27 complaints (tested sample).

---

## 2. API Call Volumes & Retry Overhead
- **Primary Invocations:** 1 API call per complaint.
  - For 100 daily complaints: **100 API calls**.
- **Retry Overhead:** The classification engine incorporates a single retry (`attempt == 0`) upon receiving malformed JSON.
  - Typical JSON failure rate with strict schema formatting: ~3% to 5%.
  - Expected retries: 3 to 5 additional calls per 100 complaints.
  - Total Daily API Calls: **~105 calls**.

---

## 3. Expected Response Latency
- **Model Selected:** Google Gemini Flash (`gemini-2.5-flash` or `gemini-1.5-flash`).
- **Input Tokens per Complaint:**
  - System prompt: ~280 tokens.
  - Complaint text + JSON wrapper: ~45 tokens.
  - Total Input: ~325 tokens.
- **Output Tokens per Complaint:**
  - JSON response structure: ~40 to 60 tokens.
- **Latency per Request:**
  - Gemini Flash average latency: **400 ms to 900 ms** per request.
  - Batch execution time for 100 complaints (sequential): **~60 to 80 seconds**.
  - Fallback deterministic classifier latency: **< 1 ms** per complaint.

---

## 4. Cost Estimates

> [!NOTE]
> Actual costs depend on the selected Gemini model tier, Google AI Studio quotas, and active Cloud billing agreements. The figures below reflect current standard Gemini 1.5/2.5 Flash pricing.

### Pricing Model (Gemini Flash Tier)
- Input: \$0.075 per 1,000,000 tokens (or Free Tier under AI Studio rate limits of 15 RPM).
- Output: \$0.300 per 1,000,000 tokens.

### Daily Cost Computation (100 Complaints)
- **Input Tokens:** 105 calls × 325 tokens = 34,125 tokens → **\$0.0026**
- **Output Tokens:** 105 calls × 50 tokens = 5,250 tokens → **\$0.0016**
- **Total Daily Cost:** **~$0.0042 USD** (Less than half a US cent per day; ₹0.35 INR).
- **Monthly Cost (22 Working Days):** **~$0.092 USD** (approx. ₹8.00 INR).

---

## 5. Summary & Economic Viability
The system is exceptionally cost-effective. Even with retries and peak student complaint spikes of 300 complaints/day, the operational cost remains under \$0.02 per day, making it an ideal high-ROI AI intervention for college transport management.
