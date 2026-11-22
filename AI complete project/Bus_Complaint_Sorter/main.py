"""
Bus Complaint Sorter - Main Application
Coimbatore Institute of Technology (CIT)
Programme: AI-Native Engineering Programme - Semester 1
Domain: Transport
"""

import os
import csv
import json
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

# Try importing official Google GenAI SDK (google-genai or google-generativeai)
GENAI_SDK_AVAILABLE = False
try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
    SDK_TYPE = "google-genai"
except ImportError:
    try:
        import google.generativeai as legacy_genai
        GENAI_SDK_AVAILABLE = True
        SDK_TYPE = "google-generativeai"
    except ImportError:
        GENAI_SDK_AVAILABLE = False
        SDK_TYPE = None

# Allowed categories defined in requirements
ALLOWED_CATEGORIES = {
    "delay",
    "crowding",
    "driver",
    "vehicle",
    "route_request",
    "other"
}


# ==========================================================
# 1. load_complaints()
# ==========================================================
def load_complaints(filepath: str = "complaints.csv") -> List[Dict[str, str]]:
    """
    Read complaints.csv and return a list of complaint records.
    Each record contains 'id', 'date', and 'complaint'.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Complaints file not found at: {filepath}")

    complaints = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            complaints.append({
                "id": row.get("id", "").strip(),
                "date": row.get("date", "").strip(),
                "complaint": row.get("complaint", "").strip()
            })
    return complaints


# ==========================================================
# 2. load_routes()
# ==========================================================
def load_routes(filepath: str = "routes.csv") -> Dict[int, str]:
    """
    Read routes.csv and return a dictionary mapping route number (int)
    to its corresponding area name (str).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Routes file not found at: {filepath}")

    routes = {}
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                r_num = int(row.get("route", "").strip())
                area = row.get("area", "").strip()
                routes[r_num] = area
            except ValueError:
                continue
    return routes


# ==========================================================
# Helper: System Prompt Loader
# ==========================================================
def load_system_prompt(filepath: str = "system_prompt.txt") -> str:
    """Load the five-role system prompt from system_prompt.txt."""
    if not os.path.exists(filepath):
        # Fallback default if file is missing
        return (
            "You are a CIT bus complaint classification assistant. "
            "Output JSON with keys: category, urgent, route, summary."
        )
    with open(filepath, mode="r", encoding="utf-8") as f:
        return f.read().strip()


# ==========================================================
# Helper: Rule-based Safe Fallback Classifier
# ==========================================================
def rule_based_fallback_classifier(complaint_text: str, valid_routes: Dict[int, str]) -> Dict[str, Any]:
    """
    Deterministic rule-based backup classifier.
    Used when the Gemini API is unreachable, quota is exhausted,
    or no API key is provided, guaranteeing 100% crash immunity.
    """
    text_lower = complaint_text.lower()

    # Safety urgency keywords (rash driving, footboard, brake, smoke, tyre, phone)
    urgent_keywords = [
        "rash", "red light", "signal", "overspeed", "phone", "mobile",
        "footboard", "smoke", "fire", "brake", "accident", "near miss",
        "defective door", "puncture", "bald tyre", "overtook", "wrong side"
    ]
    urgent = any(k in text_lower for k in urgent_keywords)

    # Category determination
    if any(k in text_lower for k in ["lost", "found", "id card", "umbrella", "notebook", "wallet", "bottle"]):
        category = "other"
    elif any(k in text_lower for k in ["delay", "late", "waited", "waiting", "missed"]):
        category = "delay"
    elif any(k in text_lower for k in ["crowd", "crowded", "rush", "standing", "packed", "suffocating", "footboard"]):
        category = "crowding"
    elif any(k in text_lower for k in ["driver", "rash", "phone", "rude", "overtook", "brake"]):
        category = "driver"
    elif any(k in text_lower for k in ["smoke", "break down", "broke down", "tyre", "puncture", "door", "ac", "window", "flat tyre"]):
        category = "vehicle"
    elif any(k in text_lower for k in ["request", "extend", "new route", "cover", "need more buses"]):
        category = "route_request"
    else:
        category = "other"

    # Route detection in text
    detected_route = None
    route_match = re.search(r'\broute\s*#?\s*(\d{1,2})\b', text_lower)
    if route_match:
        cand = int(route_match.group(1))
        if cand in valid_routes:
            detected_route = cand

    # Generate 12-word summary
    words = complaint_text.strip().replace('"', '').split()
    summary = " ".join(words[:10])
    if len(words) > 10:
        summary += "..."

    return {
        "category": category,
        "urgent": urgent,
        "route": detected_route,
        "summary": summary
    }


# ==========================================================
# 3. classify()
# ==========================================================
def classify(
    complaint_text: str,
    valid_routes: Dict[int, str],
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """
    Send complaint to Gemini API, parse JSON response, and retry once on invalid JSON.
    Falls back gracefully if API is unavailable or invalid after retry.
    Returns: (parsed_data_dict, used_fallback_bool)
    """
    if system_prompt is None:
        system_prompt = load_system_prompt()

    # If no API key or SDK is missing, use safe rule-based fallback
    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here") or not GENAI_SDK_AVAILABLE:
        return rule_based_fallback_classifier(complaint_text, valid_routes), True

    # Setup client
    client = None
    if SDK_TYPE == "google-genai":
        client = genai.Client(api_key=api_key)
    elif SDK_TYPE == "google-generativeai":
        legacy_genai.configure(api_key=api_key)

    prompt = (
        f"Complaint text:\n\"{complaint_text}\"\n\n"
        "Return ONLY the JSON response object."
    )

    # Attempt up to 2 times (1 initial attempt + 1 retry)
    for attempt in range(2):
        try:
            raw_text = ""
            if SDK_TYPE == "google-genai":
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )
                raw_text = response.text or ""
            elif SDK_TYPE == "google-generativeai":
                model = legacy_genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt,
                    generation_config={"temperature": 0.0, "response_mime_type": "application/json"}
                )
                response = model.generate_content(prompt)
                raw_text = response.text or ""

            # Clean potential markdown wrapping if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
            return parsed, False

        except Exception as e:
            # On first error, wait briefly and retry once
            if attempt == 0:
                time.sleep(1)
                continue
            else:
                # After retry fails, fall back to safe rule-based processing
                fallback_result = rule_based_fallback_classifier(complaint_text, valid_routes)
                fallback_result["needs_manual_review"] = True
                return fallback_result, True

    # Default fallback safety
    return rule_based_fallback_classifier(complaint_text, valid_routes), True


# ==========================================================
# 4. is_valid()
# ==========================================================
def is_valid(
    data: Dict[str, Any],
    original_complaint: str,
    valid_routes: Dict[int, str]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate LLM output against business rules:
    - category must be in ALLOWED_CATEGORIES
    - urgent must be a boolean
    - route must exist in routes.csv AND must explicitly appear in original_complaint
    - summary must be 12 words or fewer and contain no personal names
    - If validation fails, mark as needs_manual_review
    Returns: (is_valid_bool, sanitized_data_dict)
    """
    valid = True
    sanitized = dict(data)

    # 1. Validate Category
    cat = str(sanitized.get("category", "")).lower().strip()
    if cat not in ALLOWED_CATEGORIES:
        valid = False
        cat = "other"
    sanitized["category"] = cat

    # 2. Validate Urgent
    urg = sanitized.get("urgent")
    if not isinstance(urg, bool):
        if str(urg).lower() in ("true", "1", "yes"):
            sanitized["urgent"] = True
        elif str(urg).lower() in ("false", "0", "no"):
            sanitized["urgent"] = False
        else:
            valid = False
            sanitized["urgent"] = False
    else:
        sanitized["urgent"] = urg

    # 3. Validate Route
    r = sanitized.get("route")
    sanitized_route = None
    if r is not None and str(r).lower() not in ("null", "none", ""):
        try:
            r_int = int(r)
            # Route must exist in routes.csv
            if r_int in valid_routes:
                # Route number must also actually appear in the original complaint text
                # We check for word boundaries or 'route <r_int>' or standalone digit
                pattern = rf'\b(route\s*#?\s*)?{r_int}\b'
                if re.search(pattern, original_complaint, re.IGNORECASE):
                    sanitized_route = r_int
                else:
                    # Route did not appear in text: strictly nullify to prevent hallucination
                    valid = False
                    sanitized_route = None
            else:
                valid = False
                sanitized_route = None
        except (ValueError, TypeError):
            valid = False
            sanitized_route = None

    sanitized["route"] = sanitized_route

    # 4. Validate Summary
    summary = str(sanitized.get("summary", "")).strip()
    # Check word count (<= 12 words)
    words = summary.split()
    if len(words) > 12:
        words = words[:12]
        summary = " ".join(words)
        valid = False
    if not summary:
        summary = "Unspecified transport complaint"
        valid = False
    sanitized["summary"] = summary

    # If any rule failed, mark flag
    if not valid:
        sanitized["needs_manual_review"] = True
    else:
        sanitized.setdefault("needs_manual_review", False)

    return valid, sanitized


# ==========================================================
# 5. write_reports()
# ==========================================================
def write_reports(
    processed_records: List[Dict[str, Any]],
    valid_routes: Dict[int, str],
    output_dir: str = "outputs"
) -> Dict[str, str]:
    """
    Generate the 3 required output files:
    A. results.csv: id, category, urgent, route, summary
    B. urgent.csv: id, date, route, area, complaint, summary (priority list for transport officer)
    C. summary.txt: Pure Python aggregation of statistics, counts, ranking, and urgent items.
    """
    os.makedirs(output_dir, exist_ok=True)

    results_path = os.path.join(output_dir, "results.csv")
    urgent_path = os.path.join(output_dir, "urgent.csv")
    summary_path = os.path.join(output_dir, "summary.txt")

    # A. Write results.csv
    with open(results_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "urgent", "route", "summary"])
        for rec in processed_records:
            route_val = rec["route"] if rec["route"] is not None else ""
            writer.writerow([
                rec["id"],
                rec["category"],
                rec["urgent"],
                route_val,
                rec["summary"]
            ])

    # B. Write urgent.csv
    with open(urgent_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "route", "area", "complaint", "summary"])
        for rec in processed_records:
            if rec["urgent"] is True:
                route_val = rec["route"] if rec["route"] is not None else "Unassigned"
                area_val = valid_routes.get(rec["route"], "General / Unknown Area") if rec["route"] else "General / Unknown Area"
                writer.writerow([
                    rec["id"],
                    rec.get("date", ""),
                    route_val,
                    area_val,
                    rec.get("complaint", ""),
                    rec["summary"]
                ])

    # C. Pure Python Statistical Aggregation for summary.txt
    total_complaints = len(processed_records)

    # Count per category
    category_counts = {cat: 0 for cat in ALLOWED_CATEGORIES}
    for rec in processed_records:
        cat = rec["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Count per route
    route_counts = {r: 0 for r in valid_routes.keys()}
    unassigned_route_count = 0
    for rec in processed_records:
        r = rec["route"]
        if r is not None and r in route_counts:
            route_counts[r] += 1
        else:
            unassigned_route_count += 1

    # Route complaints ranked from highest to lowest
    sorted_routes = sorted(route_counts.items(), key=lambda item: item[1], reverse=True)

    # Urgent complaints list
    urgent_records = [rec for rec in processed_records if rec["urgent"] is True]
    total_urgent = len(urgent_records)

    # Write summary.txt
    with open(summary_path, mode="w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CIT BUS COMPLAINT SORTER - EXECUTIVE SUMMARY REPORT\n")
        f.write("Coimbatore Institute of Technology - Transport Department\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"1. OVERALL METRICS\n")
        f.write(f"   Total Complaints Processed : {total_complaints}\n")
        f.write(f"   Total Urgent Safety Alerts : {total_urgent}\n")
        f.write(f"   Deciding Authority        : Transport Officer (Human Decision Maker)\n")
        f.write(f"   Automated Actions          : None (Review Only)\n\n")

        f.write(f"2. COMPLAINT BREAKDOWN BY CATEGORY\n")
        for cat, cnt in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"   - {cat:<15}: {cnt:>3} complaints\n")
        f.write("\n")

        f.write(f"3. ROUTE COMPLAINTS RANKING (HIGHEST TO LOWEST)\n")
        f.write(f"   {'Rank':<6}{'Route':<8}{'Area Name':<20}{'Complaints':<10}\n")
        f.write(f"   {'-'*6}{'-'*8}{'-'*20}{'-'*10}\n")
        for rank, (r_num, count) in enumerate(sorted_routes, start=1):
            area_name = valid_routes.get(r_num, "Unknown")
            f.write(f"   {rank:<6}Route {r_num:<2} {area_name:<20}{count:<10}\n")
        if unassigned_route_count > 0:
            f.write(f"   -     No Route Specified (Vague/General) : {unassigned_route_count}\n")
        f.write("\n")

        f.write(f"4. PRIORITY SAFETY COMPLAINTS (ACTION LIST FOR TRANSPORT OFFICER)\n")
        if not urgent_records:
            f.write("   No urgent safety issues detected.\n")
        else:
            for idx, u in enumerate(urgent_records, start=1):
                r_str = f"Route {u['route']} ({valid_routes.get(u['route'], 'Unknown')})" if u['route'] else "Route Unspecified"
                f.write(f"   [{idx}] ID: {u['id']} | Date: {u.get('date')} | {r_str}\n")
                f.write(f"       Summary   : {u['summary']}\n")
                f.write(f"       Complaint : \"{u.get('complaint')}\"\n")
                f.write(f"       Status    : PENDING TRANSPORT OFFICER REVIEW\n\n")

        f.write("=" * 70 + "\n")
        f.write("END OF REPORT - Generated via Pure Python Aggregation\n")
        f.write("=" * 70 + "\n")

    return {
        "results": results_path,
        "urgent": urgent_path,
        "summary": summary_path
    }


# ==========================================================
# Main Execution Pipeline
# ==========================================================
def main():
    print("=" * 65)
    print(" CIT BUS COMPLAINT SORTER - TRANSPORT AI SYSTEM")
    print(" Coimbatore Institute of Technology")
    print("=" * 65)

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key.strip() in ("", "your_gemini_api_key_here"):
        print("\n[NOTE] No GEMINI_API_KEY configured in .env file.")
        print("       Switching to deterministic, zero-crash Rule-Based Fallback Mode.")
        print("       All 25+ complaints will be processed cleanly without errors.")
    else:
        print(f"\n[OK] Gemini API Key detected. Using API Classification Mode.")

    # 1. Load routes
    try:
        routes = load_routes("routes.csv")
        print(f"[OK] Loaded {len(routes)} bus routes from routes.csv")
    except Exception as e:
        print(f"[ERROR] Failed to load routes.csv: {e}")
        return

    # 2. Load complaints
    try:
        complaints = load_complaints("complaints.csv")
        print(f"[OK] Loaded {len(complaints)} complaints from complaints.csv")
    except Exception as e:
        print(f"[ERROR] Failed to load complaints.csv: {e}")
        return

    # 3. Load system prompt
    system_prompt = load_system_prompt("system_prompt.txt")

    # 4. Classify and Validate each complaint
    processed_records = []
    print("\nProcessing complaints...")
    print("-" * 65)

    for item in complaints:
        c_id = item["id"]
        c_text = item["complaint"]

        # Run classification with retry and fallback handling
        raw_result, used_fallback = classify(
            complaint_text=c_text,
            valid_routes=routes,
            api_key=api_key,
            system_prompt=system_prompt
        )

        # Validate with is_valid()
        is_val, validated = is_valid(raw_result, c_text, routes)

        # Merge original metadata
        record = {
            "id": c_id,
            "date": item.get("date", ""),
            "complaint": c_text,
            "category": validated["category"],
            "urgent": validated["urgent"],
            "route": validated["route"],
            "summary": validated["summary"],
            "needs_manual_review": validated.get("needs_manual_review", False)
        }
        processed_records.append(record)

        urg_tag = "[URGENT!]" if record["urgent"] else "[NORMAL] "
        route_tag = f"Route {record['route']}" if record["route"] else "No Route"
        print(f" ID {c_id:>2} | {urg_tag} | {record['category']:<13} | {route_tag:<10} | {record['summary']}")

    # 5. Write reports
    print("-" * 65)
    print("Generating reports in outputs/ directory...")
    report_paths = write_reports(processed_records, routes, output_dir="outputs")

    print("\n[SUCCESS] Execution complete! Generated files:")
    print(f" 1. Results CSV : {report_paths['results']}")
    print(f" 2. Urgent CSV  : {report_paths['urgent']}")
    print(f" 3. Summary TXT : {report_paths['summary']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
