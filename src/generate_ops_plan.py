"""
generate_ops_plan.py
────────────────────
Reads the berth assignment plan produced by predict_congestion.py and
renders a human-readable 72-hour port operations plan as a Markdown file
suitable for a shift supervisor briefing.

Sections produced
─────────────────
  1. Plan header   — generated timestamp, planning window, quick-read metrics
  2. Hotspot alert — any predicted congestion windows with severity and advice
  3. Vessels at risk — delayed vessels sorted by worst wait first
  4. Berth schedule — one table per berth, showing its full queue in time order
  5. Full assignment log — every vessel in ETA order with berth and timing
  6. Unassigned vessels — vessels that could not be placed (action required)
"""

import json
import os
from datetime import datetime
from collections import defaultdict


# ── File paths ─────────────────────────────────────────────────────────────────

INPUT_JSON  = os.path.join("src", "output", "berth_plan.json")
OUTPUT_MD   = os.path.join("src", "output", "ops_plan.md")


# ── Formatting helpers ─────────────────────────────────────────────────────────

def fmt_wait(minutes: int) -> str:
    """Convert a wait in minutes to a compact human string, e.g. '2 h 15 min'."""
    if minutes == 0:
        return "—"
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"{m} min"
    if m == 0:
        return f"{h} h"
    return f"{h} h {m} min"


def priority_badge(priority: str) -> str:
    """Return an uppercase label so priority tiers stand out in plain text."""
    return {"critical": "[CRITICAL]", "priority": "[PRIORITY]", "standard": "[STANDARD]"}.get(
        priority, priority.upper()
    )


def severity_badge(severity: str) -> str:
    """Map hotspot severity to a short warning tag."""
    return {"critical": "!! CRITICAL !!", "high": "! HIGH", "medium": "~ MEDIUM"}.get(
        severity, severity.upper()
    )


def hotspot_advice(berth_type: str, severity: str, utilisation: float | None) -> str:
    """
    Return a plain-language operational recommendation for a congestion hotspot.
    The advice is intentionally actionable — something a supervisor can act on
    without needing to re-read the underlying data.
    """
    ratio_str = f"{utilisation:.2f}" if utilisation is not None else "N/A (no berths free)"

    base = (
        f"Utilisation ratio {ratio_str} on {berth_type.replace('_', ' ')} berths. "
    )

    if severity == "critical" or utilisation is None:
        return base + (
            "IMMEDIATE ACTION: Consider emergency re-routing to anchorage, "
            "contacting neighbouring port for overflow capacity, or delaying "
            "non-critical vessel ETAs via port authority."
        )
    elif severity == "high":
        return base + (
            "Pre-position spare crane crews. Consider diverting one standard "
            "vessel to a compatible berth type to reduce queue depth."
        )
    else:
        return base + (
            "Monitor closely. Ensure maintenance berths are returned to service "
            "on schedule and confirm no further vessels are added to this window."
        )


# ── Section builders ───────────────────────────────────────────────────────────

def build_header(data: dict) -> list[str]:
    """
    Top-of-document section: plan metadata and key performance indicators
    laid out as a quick-read summary card.
    """
    s   = data["summary"]
    gen = data["generated_at"]
    hz  = data["planning_horizon_hours"]

    # Derive the planning window dates from the assignments list
    etas = [a["eta"] for a in data["berth_assignments"]]
    window_start = min(etas)[:10]   # just the date portion
    window_end_dt = datetime.strptime(max(etas), "%Y-%m-%d %H:%M:%S")
    window_end = window_end_dt.strftime("%Y-%m-%d")

    avg_wait = s["avg_wait_minutes_by_priority"]

    lines = [
        "# 72-Hour Port Operations Plan",
        "",
        f"> **Generated:** {gen}  ",
        f"> **Planning window:** {window_start} → {window_end} ({hz} hours)  ",
        f"> **Prepared for:** Shift Supervisor",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total vessels in window | {s['total_vessels']} |",
        f"| Vessels assigned | {s['assigned']} |",
        f"| Vessels unassigned | {s['unassigned']} |",
        f"| On schedule | {s['on_schedule_vessels']} |",
        f"| Delayed | {s['delayed_vessels']} |",
        f"| Congestion hotspots detected | {s['congestion_hotspots_detected']} |",
        f"| Avg wait — critical | {fmt_wait(int(avg_wait.get('critical', 0)))} |",
        f"| Avg wait — priority | {fmt_wait(int(avg_wait.get('priority', 0)))} |",
        f"| Avg wait — standard | {fmt_wait(int(avg_wait.get('standard', 0)))} |",
        "",
    ]
    return lines


def build_hotspots(hotspots: list[dict]) -> list[str]:
    """
    Congestion hotspot section.  Each hotspot gets its own sub-block with
    a severity badge, time window, demand/supply figures, and a supervisor
    action recommendation.
    """
    lines = [
        "---",
        "",
        "## Predicted Congestion Hotspots",
        "",
    ]

    if not hotspots:
        lines += [
            "> **No congestion hotspots detected** in the 72-hour window.",
            "> All berth types have sufficient capacity for forecast arrivals.",
            "",
        ]
        return lines

    for h in hotspots:
        badge   = severity_badge(h["severity"])
        advice  = hotspot_advice(h["berth_type"], h["severity"], h.get("utilisation_ratio"))
        ratio   = f"{h['utilisation_ratio']:.2f}" if h.get("utilisation_ratio") else "∞"

        lines += [
            f"### {badge} — {h['berth_type'].replace('_', ' ').title()} Berths",
            "",
            f"- **Window:** {h['window_start']}  →  {h['window_end']}",
            f"- **Vessels arriving:** {h['vessels_arriving']}",
            f"- **Effective berths available:** {h['berths_available']}",
            f"- **Utilisation ratio:** {ratio}  *(target ≤ 1.0)*",
            f"- **Supervisor action:** {advice}",
            "",
        ]

    return lines


def build_at_risk(assignments: list[dict]) -> list[str]:
    """
    Vessels-at-risk section: all delayed vessels sorted by longest wait first.
    Priority vessels are listed before standard ones at equal wait times so
    the supervisor's attention is drawn to the most commercially sensitive delays.
    """
    delayed = [a for a in assignments if a["wait_minutes"] > 0]

    lines = [
        "---",
        "",
        "## Vessels at Risk of Delay",
        "",
    ]

    if not delayed:
        lines += ["> All vessels are currently on schedule.", ""]
        return lines

    # Sort: longest wait first; within same wait, priority tier breaks the tie
    priority_rank = {"critical": 0, "priority": 1, "standard": 2}
    delayed_sorted = sorted(
        delayed,
        key=lambda a: (-a["wait_minutes"], priority_rank[a["priority"]])
    )

    lines += [
        f"{'Vessel':<10} {'Priority':<12} {'ETA':<18} {'Berth Start':<18} "
        f"{'Wait':<12} {'Berth':<10} {'TEU':>6}",
        "-" * 92,
    ]

    for a in delayed_sorted:
        lines.append(
            f"{a['vessel_id']:<10} {priority_badge(a['priority']):<12} "
            f"{a['eta']:<18} {a['berth_start_time']:<18} "
            f"{fmt_wait(a['wait_minutes']):<12} {a['assigned_berth']:<10} "
            f"{a['cargo_volume_teu']:>6}"
        )

    lines += ["", f"*{len(delayed)} vessel(s) will experience delays in this window.*", ""]
    return lines


def build_berth_schedules(assignments: list[dict]) -> list[str]:
    """
    Per-berth schedule section: groups assignments by berth and renders
    each berth's queue as a timetable, in chronological order.
    This gives the berth crew a single page they can pin to their board.
    """
    lines = [
        "---",
        "",
        "## Berth Schedules",
        "",
        "*Each berth's queue is shown in service order.*",
        "",
    ]

    # Group by berth
    by_berth: dict[str, list[dict]] = defaultdict(list)
    for a in assignments:
        by_berth[a["assigned_berth"]].append(a)

    for berth_id in sorted(by_berth):
        queue = sorted(by_berth[berth_id], key=lambda a: a["berth_start_time"])

        lines += [
            f"### {berth_id}",
            "",
            f"| # | Vessel | Priority | Berth Start | Berth End | TEU | Wait |",
            f"|---|--------|----------|-------------|-----------|-----|------|",
        ]

        for i, a in enumerate(queue, start=1):
            lines.append(
                f"| {i} | {a['vessel_id']} | {a['priority'].title()} "
                f"| {a['berth_start_time']} | {a['berth_end_time']} "
                f"| {a['cargo_volume_teu']:,} | {fmt_wait(a['wait_minutes'])} |"
            )

        lines += [""]

    return lines


def build_full_log(assignments: list[dict]) -> list[str]:
    """
    Complete assignment log sorted by ETA — the definitive reference table
    for the full 72-hour period.  Status column uses ON SCHEDULE / DELAYED
    labels so it can be scanned quickly.
    """
    sorted_asgn = sorted(assignments, key=lambda a: a["eta"])

    lines = [
        "---",
        "",
        "## Full Assignment Log  *(sorted by ETA)*",
        "",
        "| Vessel | Priority | ETA | Berth | Size Class | Cranes | Start | End | Wait | Status |",
        "|--------|----------|-----|-------|------------|--------|-------|-----|------|--------|",
    ]

    for a in sorted_asgn:
        status_label = "ON SCHEDULE" if a["wait_minutes"] == 0 else "DELAYED"
        lines.append(
            f"| {a['vessel_id']} | {a['priority'].title()} | {a['eta']} "
            f"| {a['assigned_berth']} | {a['berth_size_class'].replace('_', ' ').title()} "
            f"| {a['crane_count']} | {a['berth_start_time']} | {a['berth_end_time']} "
            f"| {fmt_wait(a['wait_minutes'])} | {status_label} |"
        )

    lines += [""]
    return lines


def build_unassigned(unassigned: list[dict]) -> list[str]:
    """
    Unassigned vessels section — only appears when the assignment engine
    could not find any compatible berth.  Marked as requiring operator action.
    """
    lines = [
        "---",
        "",
        "## Unassigned Vessels  *(Action Required)*",
        "",
    ]

    if not unassigned:
        lines += ["> No unassigned vessels. All incoming vessels have been placed.", ""]
        return lines

    lines += [
        "**The following vessels could not be assigned to a berth.**  ",
        "Port authority must arrange anchorage, diversion, or ETA rescheduling.",
        "",
        "| Vessel | Reason |",
        "|--------|--------|",
    ]

    for u in unassigned:
        lines.append(f"| {u['vessel_id']} | {u['reason']} |")

    lines += [""]
    return lines


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading {INPUT_JSON}...")
    with open(INPUT_JSON) as fh:
        data = json.load(fh)

    # Build each section as a list of lines, then join them all
    sections = (
        build_header(data)
        + build_hotspots(data["congestion_hotspots"])
        + build_at_risk(data["berth_assignments"])
        + build_berth_schedules(data["berth_assignments"])
        + build_full_log(data["berth_assignments"])
        + build_unassigned(data["unassigned_vessels"])
        + [
            "---",
            "",
            f"*Plan generated by predict_congestion.py / generate_ops_plan.py — "
            f"{data['generated_at']}*",
        ]
    )

    document = "\n".join(sections)

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write(document)

    print(f"Done. Operations plan written to: {OUTPUT_MD}")
    print(f"  Sections: header, hotspots, at-risk, berth schedules, full log, unassigned")


if __name__ == "__main__":
    main()
