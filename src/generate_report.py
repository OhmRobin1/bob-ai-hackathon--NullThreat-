"""
generate_report.py
==================
NullThreat Hackathon — BLUF Report Generator

This script:
  1. Reads src/output/results.json (produced by classify_alerts.py)
  2. Builds a BLUF-style (Bottom Line Up Front) Markdown report
  3. Writes the report to src/output/bluf_report.md

BLUF format (used by military and intelligence analysts):
  - Lead with the most important finding — the "so what" — before any detail.
  - Threats are ranked by severity so a reader can act on the worst first.
  - False positives are acknowledged briefly so the reader knows noise was filtered.

No API calls are made here — this is pure data transformation from the JSON file.

Usage:
  python src/generate_report.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Severity ordering
#    We use this to sort threats from most dangerous → least dangerous.
# ---------------------------------------------------------------------------
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}

# Emoji badges make the severity levels easy to scan in rendered Markdown.
SEVERITY_BADGE = {
    "critical": "🔴 CRITICAL",
    "high":     "🟠 HIGH",
    "medium":   "🟡 MEDIUM",
    "low":      "🟢 LOW",
}


# ---------------------------------------------------------------------------
# 2. Helper — pick the single most prominent incident for the BLUF headline
# ---------------------------------------------------------------------------
def top_incident_summary(incidents: list) -> str:
    """
    Return a one-line string describing the most severe incident group.
    Used in the opening BLUF paragraph.
    """
    if not incidents:
        return "no confirmed threat incidents"

    # incidents are already sorted by severity in build_report(), but sort
    # defensively here too just in case this helper is called standalone.
    ranked = sorted(incidents, key=lambda i: SEVERITY_RANK.get(i.get("severity_max", "unknown"), 4))
    top = ranked[0]
    count = top["alert_count"]
    technique = top.get("mitre_technique", top.get("mitre_label", "unknown technique"))
    sev = top.get("severity_max", "unknown").upper()
    return f"{count} correlated {sev}-severity alert(s) mapped to {technique}"


# ---------------------------------------------------------------------------
# 3. Core report builder — returns the full Markdown string
# ---------------------------------------------------------------------------
def build_report(data: dict) -> str:
    """
    Takes the parsed results.json dict and returns a BLUF Markdown string.

    Structure:
      [HEADER]
      [BLUF — 2-3 sentence bottom line]
      [CONFIRMED THREATS — table ranked by severity]
      [INCIDENT GROUPS — correlated alert clusters]
      [FALSE POSITIVES — brief summary table]
      [FOOTER — metadata]
    """

    # --- Unpack the three top-level sections of results.json ---
    meta      = data.get("run_metadata", {})
    alerts    = data.get("alerts", [])
    incidents = data.get("incidents", [])

    # --- Separate real threats from false positives ---
    threats = [a for a in alerts if a.get("classification") == "real_threat"]
    fps     = [a for a in alerts if a.get("classification") == "false_positive"]

    # Sort threats: critical first, then high, medium, low
    threats_sorted = sorted(threats, key=lambda a: SEVERITY_RANK.get(a.get("severity", "unknown"), 4))

    # Sort incidents the same way
    incidents_sorted = sorted(incidents, key=lambda i: SEVERITY_RANK.get(i.get("severity_max", "unknown"), 4))

    # --- Counts for the BLUF paragraph ---
    total         = meta.get("total_alerts", len(alerts))
    threat_count  = meta.get("real_threats", len(threats))
    fp_count      = meta.get("false_positives", len(fps))
    inc_count     = meta.get("incident_groups", len(incidents))
    top_summary   = top_incident_summary(incidents_sorted)

    # Highest severity present across all real threats
    top_sev = threats_sorted[0]["severity"].upper() if threats_sorted else "N/A"

    # Report generation timestamp
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # -----------------------------------------------------------------------
    # Build the Markdown document section by section.
    # We use a list of lines and join at the end — easier to maintain than
    # one giant f-string.
    # -----------------------------------------------------------------------
    lines = []

    # === HEADER ===
    lines += [
        "# NullThreat — Threat Intelligence BLUF Report",
        f"**Generated:** {generated_at}  ",
        f"**Model:** {meta.get('model', 'N/A')}  ",
        f"**Alerts analysed:** {total}",
        "",
        "---",
        "",
    ]

    # === BLUF SECTION ===
    # This is the most important part — the 2-3 sentence bottom line.
    lines += [
        "## ⚡ Bottom Line Up Front (BLUF)",
        "",
    ]

    if threat_count == 0:
        lines += [
            f"Of {total} ingested alerts, **no confirmed threats** were identified; "
            f"all {fp_count} alerts were classified as false positives. "
            "No immediate action is required, but continued monitoring is advised.",
            "",
        ]
    else:
        lines += [
            f"Of **{total} alerts** analysed, **{threat_count} confirmed threats** were identified "
            f"across **{inc_count} incident group(s)**, with the highest severity reaching **{top_sev}**. "
            f"The most significant cluster involves {top_summary}. "
            f"**Immediate analyst review and response is required.** "
            f"The remaining {fp_count} alerts were assessed as false positives and discarded.",
            "",
        ]

    lines += ["---", ""]

    # === CONFIRMED THREATS TABLE ===
    lines += [
        f"## 🚨 Confirmed Threats ({threat_count})",
        "",
        "Ranked by severity — highest risk first.",
        "",
        "| # | Alert ID | Timestamp | Source | Severity | MITRE ATT&CK Technique | Confidence | Summary |",
        "|---|----------|-----------|--------|----------|------------------------|------------|---------|",
    ]

    for rank, alert in enumerate(threats_sorted, start=1):
        sev_badge  = SEVERITY_BADGE.get(alert.get("severity", ""), alert.get("severity", "").upper())
        technique  = alert.get("mitre_technique") or "—"
        confidence = alert.get("confidence", "—").capitalize()
        # Truncate long descriptions to keep the table readable
        desc = alert.get("description", "")
        short_desc = (desc[:90] + "…") if len(desc) > 90 else desc

        lines.append(
            f"| {rank} "
            f"| {alert.get('alert_id', '—')} "
            f"| {alert.get('timestamp', '—')} "
            f"| {alert.get('source_system', '—')} "
            f"| {sev_badge} "
            f"| {technique} "
            f"| {confidence} "
            f"| {short_desc} |"
        )

    lines += ["", "---", ""]

    # === INCIDENT GROUPS SECTION ===
    lines += [
        f"## 🔗 Correlated Incident Groups ({inc_count})",
        "",
        "Alerts grouped by shared MITRE ATT&CK technique — likely parts of the same attack chain.",
        "",
    ]

    if not incidents_sorted:
        lines += ["_No incident groups identified._", ""]
    else:
        for inc in incidents_sorted:
            sev_badge  = SEVERITY_BADGE.get(inc.get("severity_max", ""), inc.get("severity_max", "").upper())
            technique  = inc.get("mitre_technique", inc.get("mitre_label", "Unknown"))
            alert_ids  = ", ".join(inc.get("alert_ids", []))
            count      = inc.get("alert_count", 0)

            lines += [
                f"### {inc['incident_id']} — {technique}",
                f"- **Max Severity:** {sev_badge}",
                f"- **Alert Count:** {count}",
                f"- **Constituent Alerts:** {alert_ids}",
                "",
            ]

    lines += ["---", ""]

    # === FALSE POSITIVES SECTION ===
    lines += [
        f"## ✅ Discarded False Positives ({fp_count})",
        "",
        "The following alerts were assessed as benign or routine activity and require no action.",
        "",
        "| Alert ID | Timestamp | Source | Severity | Description |",
        "|----------|-----------|--------|----------|-------------|",
    ]

    # Sort false positives by timestamp for easy reading
    fps_sorted = sorted(fps, key=lambda a: a.get("timestamp", ""))
    for alert in fps_sorted:
        desc = alert.get("description", "")
        short_desc = (desc[:80] + "…") if len(desc) > 80 else desc
        lines.append(
            f"| {alert.get('alert_id', '—')} "
            f"| {alert.get('timestamp', '—')} "
            f"| {alert.get('source_system', '—')} "
            f"| {alert.get('severity', '—')} "
            f"| {short_desc} |"
        )

    lines += ["", "---", ""]

    # === FOOTER ===
    lines += [
        "## 📊 Summary Statistics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total alerts ingested | {total} |",
        f"| Confirmed threats | {threat_count} |",
        f"| False positives discarded | {fp_count} |",
        f"| Incident groups | {inc_count} |",
        f"| Signal-to-noise ratio | {threat_count}/{total} ({100 * threat_count // total if total else 0}%) |",
        f"| Highest severity observed | {top_sev} |",
        "",
        "---",
        "",
        "_This report was generated automatically by the NullThreat AI pipeline "
        "using IBM watsonx.ai. All classifications should be reviewed by a qualified "
        "security analyst before operational decisions are made._",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Main — load JSON, build report, write Markdown file
# ---------------------------------------------------------------------------
def main():
    output_dir  = Path(__file__).parent / "output"
    input_json  = output_dir / "results.json"
    output_md   = output_dir / "bluf_report.md"

    # --- Check the input file exists ---
    if not input_json.exists():
        raise FileNotFoundError(
            f"Cannot find {input_json}.\n"
            "Run classify_alerts.py first to generate results.json."
        )

    # --- Load results.json ---
    print(f"[1/3] Reading {input_json} ...")
    with open(input_json, encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("run_metadata", {})
    print(f"      {meta.get('total_alerts', '?')} alerts — "
          f"{meta.get('real_threats', '?')} threats — "
          f"{meta.get('false_positives', '?')} false positives")

    # --- Build the Markdown report ---
    print(f"[2/3] Building BLUF report ...")
    report_md = build_report(data)

    # --- Write to file ---
    print(f"[3/3] Writing {output_md} ...")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nReport written to {output_md}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
