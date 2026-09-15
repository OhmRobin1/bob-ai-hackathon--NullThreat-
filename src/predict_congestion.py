"""
predict_congestion.py
─────────────────────
Reads incoming vessel arrival records and current berth availability,
then does two things:

  1. CONGESTION PREDICTION
     Scans a 72-hour window in 6-hour slices and counts how many vessels
     are competing for the same berth type vs. how many suitable berths
     are actually free in that slice.  A slice whose demand exceeds supply
     is flagged as a congestion hotspot.

  2. BERTH ASSIGNMENT OPTIMISATION
     Assigns every incoming vessel to the best available berth, working
     through vessels in priority order (critical → priority → standard)
     so that high-value cargo is never blocked by routine traffic.

Results are written to src/output/berth_plan.json.
"""

import csv
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict


# ── Constants ──────────────────────────────────────────────────────────────────

# Where the data files live
VESSELS_CSV = os.path.join("src", "data", "vessels.csv")
BERTHS_CSV  = os.path.join("src", "data", "berths.csv")
OUTPUT_JSON = os.path.join("src", "output", "berth_plan.json")

# How far ahead (in hours) we look for congestion
PLANNING_HORIZON_HOURS = 72

# Each berth occupancy is modelled as a fixed service time (hours per vessel).
# In a real system this would be derived from TEU volume and crane throughput.
BERTH_SERVICE_TIME_HOURS = 8

# Priority ranking — lower number = higher urgency
PRIORITY_ORDER = {"critical": 0, "priority": 1, "standard": 2}

# Which berth size classes can accommodate which requested berth types.
# A vessel asking for "general" can go to any medium-or-larger berth.
# A vessel asking for "deep_water" needs large or ultra_large capacity.
# A vessel asking for "shallow_water" can use any size.
COMPATIBILITY = {
    "shallow_water": {"small", "medium", "large", "ultra_large"},
    "general":       {"medium", "large", "ultra_large"},
    "deep_water":    {"large", "ultra_large"},
}

# Timestamp format used in both CSV files
TS_FORMAT = "%Y-%m-%d %H:%M:%S"


# ── Data loading ───────────────────────────────────────────────────────────────

def load_vessels(path: str) -> list[dict]:
    """
    Read vessels.csv and return a list of vessel dicts.
    The 'eta' field is converted from a string to a datetime object so we
    can do arithmetic on it later.  'cargo_volume_teu' is cast to int.
    """
    vessels = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            row["eta"]              = datetime.strptime(row["eta"], TS_FORMAT)
            row["cargo_volume_teu"] = int(row["cargo_volume_teu"])
            vessels.append(row)
    return vessels


def load_berths(path: str) -> list[dict]:
    """
    Read berths.csv and return a list of berth dicts.
    'crane_count' is cast to int and 'next_available_time' becomes a datetime.
    """
    berths = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            row["crane_count"]        = int(row["crane_count"])
            row["next_available_time"] = datetime.strptime(
                row["next_available_time"], TS_FORMAT
            )
            berths.append(row)
    return berths


# ── Congestion prediction ──────────────────────────────────────────────────────

def predict_congestion(
    vessels: list[dict],
    berths:  list[dict],
    horizon_hours: int = PLANNING_HORIZON_HOURS,
    slice_hours:   int = 6,
) -> list[dict]:
    """
    Divide the planning window into equal time slices and, for each slice,
    compare how many vessels are arriving against how many compatible berths
    will be free.

    Returns a list of hotspot records — one per (time_slice, berth_type)
    combination where demand > supply.

    Parameters
    ----------
    vessels       : loaded vessel list
    berths        : loaded berth list
    horizon_hours : total hours to scan (default 72)
    slice_hours   : width of each time bucket (default 6 h)
    """
    # Anchor the window to the earliest ETA in the dataset so the analysis
    # is relative to actual arrivals rather than wall-clock time.
    window_start = min(v["eta"] for v in vessels)
    window_end   = window_start + timedelta(hours=horizon_hours)

    # Build the list of slice boundaries: [(t0, t1), (t1, t2), ...]
    slices = []
    t = window_start
    while t < window_end:
        slices.append((t, t + timedelta(hours=slice_hours)))
        t += timedelta(hours=slice_hours)

    hotspots = []

    for slice_start, slice_end in slices:
        # Count arriving vessels per requested berth type in this slice
        demand: dict[str, int] = defaultdict(int)
        for v in vessels:
            if slice_start <= v["eta"] < slice_end:
                demand[v["requested_berth_type"]] += 1

        if not any(demand.values()):
            continue  # no arrivals in this window, nothing to analyse

        # Count available (non-maintenance) berths per type for this slice.
        # A berth scores 1.0 if it is free at the slice START (fully available),
        # 0.5 if it frees up mid-slice (partial credit — handles only some arrivals),
        # and 0.0 if it is still occupied/in-maintenance for the whole slice.
        # Using fractional weights gives a more realistic utilisation ratio
        # than simply counting every berth that becomes free at any point.
        supply: dict[str, float] = defaultdict(float)
        for b in berths:
            if b["current_status"] == "maintenance":
                continue  # maintenance berths cannot take any vessel
            nat = b["next_available_time"]
            if nat <= slice_start:
                weight = 1.0   # fully available from the start of the slice
            elif nat < slice_end:
                weight = 0.5   # frees up partway through — partial credit
            else:
                continue       # not available at all during this slice
            for berth_type, allowed_sizes in COMPATIBILITY.items():
                if b["max_vessel_size"] in allowed_sizes:
                    supply[berth_type] += weight

        # Compare demand vs supply for every berth type that has arrivals
        for berth_type, arriving in demand.items():
            available = supply.get(berth_type, 0)
            utilisation = round(arriving / available, 2) if available > 0 else None

            if available == 0 or arriving > available:
                hotspots.append({
                    "window_start":   slice_start.strftime(TS_FORMAT),
                    "window_end":     slice_end.strftime(TS_FORMAT),
                    "berth_type":     berth_type,
                    "vessels_arriving": arriving,
                    "berths_available": available,
                    "utilisation_ratio": utilisation,
                    "severity": (
                        "critical" if (utilisation is None or utilisation >= 2.0)
                        else "high"  if utilisation >= 1.5
                        else "medium"
                    ),
                })

    return hotspots


# ── Berth assignment optimisation ─────────────────────────────────────────────

def assign_berths(
    vessels: list[dict],
    berths:  list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Assign each vessel to the most suitable available berth, processing
    vessels from highest to lowest priority so that critical cargo is never
    kept waiting by standard cargo.

    The assignment model:
      - A berth must be compatible with the vessel's requested_berth_type.
      - A berth must be free (next_available_time ≤ vessel ETA), unless the
        vessel is critical — critical vessels get the berth with the soonest
        next_available_time even if it means a short wait.
      - Among eligible berths, prefer the one with the most cranes (faster
        turnaround) and the smallest size overshoot (don't waste capacity).
      - After assignment, the berth's next_available_time is advanced by
        BERTH_SERVICE_TIME_HOURS so subsequent vessels see the updated state.

    Returns
    -------
    assignments : list of assignment records (one per vessel)
    unassigned  : list of vessels that could not be placed
    """
    # Sort vessels: critical first, then priority, then standard.
    # Within the same priority tier, earlier ETA comes first.
    sorted_vessels = sorted(
        vessels,
        key=lambda v: (PRIORITY_ORDER[v["priority"]], v["eta"])
    )

    # Work on a mutable copy of berth state so we don't alter the input list.
    # We track next_available_time per berth as we assign vessels to it.
    berth_state = {
        b["berth_id"]: {
            "crane_count":        b["crane_count"],
            "max_vessel_size":    b["max_vessel_size"],
            "current_status":     b["current_status"],
            "next_available_time": b["next_available_time"],
        }
        for b in berths
    }

    # Size rank used to compute "overshoot" — a large berth given to a small
    # vessel wastes capacity that might be needed for bigger ships later.
    SIZE_RANK = {"small": 0, "medium": 1, "large": 2, "ultra_large": 3}

    assignments = []
    unassigned  = []

    for vessel in sorted_vessels:
        berth_type   = vessel["requested_berth_type"]
        allowed_sizes = COMPATIBILITY[berth_type]
        eta           = vessel["eta"]
        is_critical   = vessel["priority"] == "critical"

        # Gather candidate berths that:
        #   (a) are not in maintenance
        #   (b) have a compatible size class
        candidates = [
            (bid, state)
            for bid, state in berth_state.items()
            if state["current_status"] != "maintenance"
            and state["max_vessel_size"] in allowed_sizes
        ]

        if not candidates:
            # No compatible berth exists at all — vessel cannot be placed
            unassigned.append({
                "vessel_id": vessel["vessel_id"],
                "reason": f"No compatible berth for type '{berth_type}'",
            })
            continue

        # Separate candidates into immediately available (ready before ETA)
        # and those requiring a wait.
        ready    = [(bid, s) for bid, s in candidates if s["next_available_time"] <= eta]
        waiting  = [(bid, s) for bid, s in candidates if s["next_available_time"] >  eta]

        if ready:
            # Pick the best ready berth:
            #   primary key   → most cranes (faster handling)
            #   secondary key → least size overshoot (preserve big berths)
            chosen_id, chosen_state = max(
                ready,
                key=lambda x: (
                    x[1]["crane_count"],
                    -SIZE_RANK[x[1]["max_vessel_size"]],
                )
            )
            wait_minutes = 0
            actual_start = eta

        elif is_critical and waiting:
            # Critical vessel: accept a wait and take the soonest-free berth.
            chosen_id, chosen_state = min(
                waiting,
                key=lambda x: x[1]["next_available_time"]
            )
            actual_start  = chosen_state["next_available_time"]
            wait_minutes  = int((actual_start - eta).total_seconds() / 60)

        else:
            # Non-critical vessel with no berth immediately ready.
            # Still assign it to the soonest-free compatible berth, but flag
            # the wait so operators know the vessel will be anchored.
            chosen_id, chosen_state = min(
                waiting,
                key=lambda x: x[1]["next_available_time"]
            )
            actual_start  = chosen_state["next_available_time"]
            wait_minutes  = int((actual_start - eta).total_seconds() / 60)

        # Compute when this berth will next be free after this vessel leaves.
        departure_time = actual_start + timedelta(hours=BERTH_SERVICE_TIME_HOURS)

        # Update the berth's availability so the next vessel in the loop
        # sees the correct state (the berth is now occupied until departure).
        berth_state[chosen_id]["next_available_time"] = departure_time
        berth_state[chosen_id]["current_status"]      = "occupied"

        assignments.append({
            "vessel_id":         vessel["vessel_id"],
            "priority":          vessel["priority"],
            "cargo_volume_teu":  vessel["cargo_volume_teu"],
            "requested_berth_type": berth_type,
            "eta":               eta.strftime(TS_FORMAT),
            "assigned_berth":    chosen_id,
            "berth_size_class":  chosen_state["max_vessel_size"],
            "crane_count":       chosen_state["crane_count"],
            "berth_start_time":  actual_start.strftime(TS_FORMAT),
            "berth_end_time":    departure_time.strftime(TS_FORMAT),
            "wait_minutes":      wait_minutes,
            "status": (
                "on_schedule" if wait_minutes == 0
                else "delayed_critical" if is_critical
                else "delayed"
            ),
        })

    return assignments, unassigned


# ── Summary statistics ─────────────────────────────────────────────────────────

def build_summary(
    assignments: list[dict],
    unassigned:  list[dict],
    hotspots:    list[dict],
) -> dict:
    """
    Produce a high-level summary block that gives port operators a quick
    operational picture without needing to parse every assignment record.
    """
    total = len(assignments) + len(unassigned)

    # Average wait grouped by priority tier
    wait_by_priority: dict[str, list[int]] = defaultdict(list)
    for a in assignments:
        wait_by_priority[a["priority"]].append(a["wait_minutes"])

    avg_wait = {
        p: round(sum(waits) / len(waits), 1)
        for p, waits in wait_by_priority.items()
    }

    delayed = [a for a in assignments if a["wait_minutes"] > 0]

    return {
        "total_vessels":        total,
        "assigned":             len(assignments),
        "unassigned":           len(unassigned),
        "delayed_vessels":      len(delayed),
        "on_schedule_vessels":  len(assignments) - len(delayed),
        "avg_wait_minutes_by_priority": avg_wait,
        "congestion_hotspots_detected": len(hotspots),
        "critical_hotspots":    sum(1 for h in hotspots if h["severity"] == "critical"),
        "high_hotspots":        sum(1 for h in hotspots if h["severity"] == "high"),
        "medium_hotspots":      sum(1 for h in hotspots if h["severity"] == "medium"),
    }


# ── Main entry point ───────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    vessels = load_vessels(VESSELS_CSV)
    berths  = load_berths(BERTHS_CSV)
    print(f"  {len(vessels)} vessels loaded, {len(berths)} berths loaded.")

    print("Predicting congestion hotspots (72-hour window)...")
    hotspots = predict_congestion(vessels, berths)
    print(f"  {len(hotspots)} hotspot window(s) detected.")

    print("Optimising berth assignments (critical -> priority -> standard)...")
    assignments, unassigned = assign_berths(vessels, berths)
    print(f"  {len(assignments)} assigned, {len(unassigned)} could not be placed.")

    summary = build_summary(assignments, unassigned, hotspots)

    # Assemble the final output document
    output = {
        "generated_at":    datetime.now().strftime(TS_FORMAT),
        "planning_horizon_hours": PLANNING_HORIZON_HOURS,
        "summary":         summary,
        "congestion_hotspots": hotspots,
        "berth_assignments":   assignments,
        "unassigned_vessels":  unassigned,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"\nDone. Results written to: {OUTPUT_JSON}")
    print(f"  Summary: {summary}")


if __name__ == "__main__":
    main()
