"""
classify_alerts.py
==================
NullThreat Hackathon — Security Alert Classifier

This script:
  1. Reads simulated security alerts from src/data/alerts.csv
  2. Classifies each alert as 'false_positive' or 'real_threat'
     - DEMO MODE  (default) : uses a built-in rule-based classifier — no API key needed
     - WATSONX MODE         : calls IBM watsonx.ai LLM — requires credentials in src/.env
  3. Maps real threats to a MITRE ATT&CK technique
  4. Groups correlated alerts that appear to be part of the same incident
  5. Writes a structured JSON report to src/output/results.json

Switch modes by setting MODE = "watsonx" or MODE = "demo" near the top of this file,
or by setting the environment variable CLASSIFY_MODE=watsonx in your .env file.

Prerequisites (only needed for watsonx mode):
  pip install ibm-watsonx-ai python-dotenv
"""

import csv
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 0. Load environment variables (silently — no crash if .env is missing)
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)
load_dotenv(override=False)  # fallback: root-level .env

# ---------------------------------------------------------------------------
# MODE SWITCH
#   "demo"    — rule-based classifier, no API key, works offline
#   "watsonx" — calls IBM watsonx.ai LLM (requires WATSONX_API_KEY etc.)
# ---------------------------------------------------------------------------
MODE = os.getenv("CLASSIFY_MODE", "demo").lower()   # default: demo

WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

if MODE == "watsonx" and (not WATSONX_API_KEY or not WATSONX_PROJECT_ID):
    raise EnvironmentError(
        "CLASSIFY_MODE=watsonx but WATSONX_API_KEY or WATSONX_PROJECT_ID is missing.\n"
        "Copy src/.env.example to src/.env and fill in your credentials,\n"
        "or leave CLASSIFY_MODE unset to use demo (offline) mode."
    )

# ---------------------------------------------------------------------------
# 1. MITRE ATT&CK reference table
#    Maps short keyword labels → full technique ID + name strings.
# ---------------------------------------------------------------------------
MITRE_TECHNIQUES = {
    "phishing":             "T1566 - Phishing",
    "valid_accounts":       "T1078 - Valid Accounts",
    "application_protocol": "T1071 - Application Layer Protocol",
    "lateral_movement_smb": "T1021.002 - Remote Services: SMB/Windows Admin Shares",
    "credential_dumping":   "T1003 - OS Credential Dumping",
    "powershell":           "T1059.001 - Command and Scripting Interpreter: PowerShell",
    "data_exfiltration":    "T1041 - Exfiltration Over C2 Channel",
    "usb_exfil":            "T1052.001 - Exfiltration Over Physical Medium: USB",
    "exploit_public_app":   "T1190 - Exploit Public-Facing Application",
    "privilege_escalation": "T1068 - Exploitation for Privilege Escalation",
}

MITRE_LIST_FOR_PROMPT = "\n".join(
    f"  - {label}: {full}" for label, full in MITRE_TECHNIQUES.items()
)

# ===========================================================================
# DEMO MODE — rule-based classifier
# ===========================================================================
# Each rule is a tuple of:
#   (keyword_to_search_in_description,  mitre_label,        reason_string)
# Rules are checked in order; first match wins.
# If no rule matches → false_positive.
# ===========================================================================
THREAT_RULES = [
    # keyword (lowercase)                mitre_label               reason
    ("c2 server",                        "application_protocol",   "Traffic to known C2 server detected"),
    ("dga domain",                       "application_protocol",   "DGA domain pattern indicates C2 beaconing"),
    ("beaconing",                        "application_protocol",   "Periodic beaconing behaviour suggests C2 channel"),
    ("phishing",                         "phishing",               "Phishing campaign or click-through detected"),
    ("malicious link",                   "phishing",               "User interaction with malicious link confirmed"),
    ("lateral movement",                 "lateral_movement_smb",   "SMB-based lateral movement across internal hosts"),
    ("smb enumeration",                  "lateral_movement_smb",   "SMB enumeration consistent with lateral movement"),
    ("mimikatz",                         "credential_dumping",     "Mimikatz signature indicates credential dumping"),
    ("credential dump",                  "credential_dumping",     "In-memory credential dumping tool detected"),
    ("powershell",                       "powershell",             "Encoded PowerShell execution is suspicious"),
    ("encoded command",                  "powershell",             "Encoded command via PowerShell detected"),
    ("exfiltration",                     "data_exfiltration",      "Data exfiltration attempt detected"),
    ("large archive",                    "data_exfiltration",      "Large file transfer to external storage detected"),
    ("usb",                              "usb_exfil",              "Unauthorized USB device on sensitive system"),
    ("exploit",                          "exploit_public_app",     "Active exploitation of public-facing application"),
    ("reverse shell",                    "exploit_public_app",     "Reverse shell established via public exploit"),
    ("privilege escalation",             "privilege_escalation",   "Privilege escalation without change ticket"),
    ("elevated to local admin",          "privilege_escalation",   "Unauthorized local admin elevation detected"),
    ("ransomware",                       "data_exfiltration",      "Ransomware-like encryption activity detected"),
    ("zero-day",                         "exploit_public_app",     "Unpatched device vulnerable to disclosed zero-day"),
    ("nation-state",                     "application_protocol",   "Nation-state TTP pattern matched in traffic"),
    ("failed ssh",                       "valid_accounts",         "Repeated SSH failures suggest brute-force attempt"),
    ("multiple failed",                  "valid_accounts",         "Multiple auth failures indicate credential attack"),
    ("repeated authentication failures", "valid_accounts",         "Service account auth failures — possible misuse"),
    ("unusual outbound traffic",         "data_exfiltration",      "Anomalous outbound volume to external IP"),
]

def rule_based_classify(alert: dict) -> dict:
    """
    Apply keyword rules against the alert description to decide
    false_positive vs real_threat without any API call.

    Returns the same dict shape as the watsonx classifier so the rest
    of the pipeline works identically in both modes.
    """
    desc_lower = alert.get("description", "").lower()

    for keyword, mitre_label, reason in THREAT_RULES:
        if keyword in desc_lower:
            return {
                "alert_id":        alert["alert_id"],
                "timestamp":       alert["timestamp"],
                "source_system":   alert["source_system"],
                "severity":        alert["severity"],
                "description":     alert["description"],
                "classification":  "real_threat",
                "confidence":      "high",
                "mitre_label":     mitre_label,
                "mitre_technique": MITRE_TECHNIQUES[mitre_label],
                "reason":          reason,
            }

    # No threat keyword matched → benign / false positive
    return {
        "alert_id":        alert["alert_id"],
        "timestamp":       alert["timestamp"],
        "source_system":   alert["source_system"],
        "severity":        alert["severity"],
        "description":     alert["description"],
        "classification":  "false_positive",
        "confidence":      "high",
        "mitre_label":     None,
        "mitre_technique": None,
        "reason":          "No threat indicators matched; assessed as routine or benign activity.",
    }


# ===========================================================================
# WATSONX MODE — LLM classifier
# ===========================================================================

def _init_watsonx_model():
    """Lazily initialise the watsonx model only when watsonx mode is active."""
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params

    credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
    model = ModelInference(
        model_id="meta-llama/llama-3-3-70b-instruct",
        credentials=credentials,
        project_id=WATSONX_PROJECT_ID,
        params={
            Params.MAX_NEW_TOKENS: 300,
            Params.TEMPERATURE:    0.1,
            Params.STOP_SEQUENCES: ["---"],
        },
    )
    return model


def build_prompt(alert: dict) -> str:
    """Build the zero-shot classification prompt for a single alert."""
    return f"""You are a cybersecurity analyst for a defense threat-intelligence system.

Analyze the following security alert and respond with ONLY a JSON object — no explanation.

Alert details:
  alert_id    : {alert['alert_id']}
  timestamp   : {alert['timestamp']}
  source      : {alert['source_system']}
  severity    : {alert['severity']}
  description : {alert['description']}

Respond using this exact JSON structure:
{{
  "classification": "<false_positive | real_threat>",
  "confidence":     "<low | medium | high>",
  "mitre_label":    "<one key from the list below, or null if false_positive>",
  "reason":         "<one sentence explaining your decision>"
}}

MITRE technique labels you may use:
{MITRE_LIST_FOR_PROMPT}

JSON response:
"""


def watsonx_classify(alert: dict, model) -> dict:
    """Call watsonx.ai and parse the classification response."""
    prompt   = build_prompt(alert)
    response = model.generate_text(prompt=prompt)
    raw_text = response.strip() if isinstance(response, str) else ""

    # Strip markdown fences if present
    raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"\n?```$", "", raw_text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    mitre_label     = result.get("mitre_label") or None
    mitre_technique = MITRE_TECHNIQUES.get(mitre_label) if mitre_label else None

    return {
        "alert_id":        alert["alert_id"],
        "timestamp":       alert["timestamp"],
        "source_system":   alert["source_system"],
        "severity":        alert["severity"],
        "description":     alert["description"],
        "classification":  result.get("classification", "unknown").lower(),
        "confidence":      result.get("confidence", "unknown").lower(),
        "mitre_label":     mitre_label,
        "mitre_technique": mitre_technique,
        "reason":          result.get("reason", "No reason provided."),
    }


# ---------------------------------------------------------------------------
# 5. Correlation — group real_threat alerts by shared MITRE technique
# ---------------------------------------------------------------------------
def correlate_incidents(classified_alerts: list) -> list:
    """
    Walk through real_threat alerts and group them by MITRE technique label.
    Each group becomes one incident.
    """
    SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    buckets: dict = {}
    for alert in classified_alerts:
        if alert["classification"] != "real_threat":
            continue
        label = alert.get("mitre_label") or "unknown"
        buckets.setdefault(label, []).append(alert)

    incidents = []
    for idx, (label, group) in enumerate(sorted(buckets.items()), start=1):
        max_alert = max(group, key=lambda a: SEV_ORDER.get(a["severity"], 0))
        incidents.append({
            "incident_id":     f"INC-{idx:03d}",
            "mitre_label":     label,
            "mitre_technique": MITRE_TECHNIQUES.get(label, label),
            "alert_ids":       [a["alert_id"] for a in group],
            "alert_count":     len(group),
            "severity_max":    max_alert["severity"],
        })
    return incidents


# ---------------------------------------------------------------------------
# 6. Main pipeline
# ---------------------------------------------------------------------------
def main():
    data_dir    = Path(__file__).parent / "data"
    output_dir  = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_csv   = data_dir   / "alerts.csv"
    output_json = output_dir / "results.json"

    # --- Step A: Read CSV ---
    print(f"[1/4] Reading alerts from {input_csv} ...")
    alerts = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            alerts.append(row)
    print(f"      Loaded {len(alerts)} alerts.")

    # --- Step B: Classify ---
    if MODE == "watsonx":
        print(f"\n[2/4] MODE: watsonx.ai  (meta-llama/llama-3-3-70b-instruct)")
        model = _init_watsonx_model()
    else:
        print(f"\n[2/4] MODE: demo (rule-based, offline — no API key needed)")
        model = None

    classified = []
    for i, alert in enumerate(alerts, start=1):
        print(f"      [{i:02d}/{len(alerts)}] {alert['alert_id']}  {alert['severity']:8s}  ", end="", flush=True)

        if MODE == "watsonx":
            result = watsonx_classify(alert, model)
            time.sleep(0.5)   # respect rate limits
        else:
            result = rule_based_classify(alert)

        label = result["classification"]
        mitre = result.get("mitre_technique") or "—"
        print(f"{label}  |  {mitre}")
        classified.append(result)

    # --- Step C: Correlate ---
    print(f"\n[3/4] Correlating real threats into incidents ...")
    incidents = correlate_incidents(classified)
    print(f"      Found {len(incidents)} incident group(s).")

    # --- Step D: Write JSON ---
    print(f"\n[4/4] Writing {output_json} ...")
    real_threats    = sum(1 for a in classified if a["classification"] == "real_threat")
    false_positives = sum(1 for a in classified if a["classification"] == "false_positive")

    output = {
        "run_metadata": {
            "model":           f"rule-based-demo" if MODE == "demo" else "meta-llama/llama-3-3-70b-instruct",
            "mode":            MODE,
            "total_alerts":    len(classified),
            "real_threats":    real_threats,
            "false_positives": false_positives,
            "incident_groups": len(incidents),
        },
        "alerts":    classified,
        "incidents": incidents,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone!")
    print(f"   Real threats   : {real_threats}")
    print(f"   False positives: {false_positives}")
    print(f"   Incident groups: {len(incidents)}")
    print(f"   Output         : {output_json}")


if __name__ == "__main__":
    main()
