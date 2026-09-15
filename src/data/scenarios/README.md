# PortWise Demo Scenarios

Three ready-to-run dataset pairs for live demonstrations.
Each pair is a `vessels.csv` + `berths.csv` that produces a visually distinct
outcome when fed into `predict_congestion.py`.

---

## How to switch scenarios

1. Copy the scenario files over the live data files:

```bash
# Example — load Scenario 2
copy src\data\scenarios\scenario_2_critical_surge\vessels.csv src\data\vessels.csv
copy src\data\scenarios\scenario_2_critical_surge\berths.csv  src\data\berths.csv
```

2. Re-run the pipeline:

```bash
python src/predict_congestion.py
python src/generate_ops_plan.py
```

3. Open `src/output/ops_plan.md` or `src/dashboard/index.html` to show results.

---

## Scenario Summaries

### Scenario 1 — Peak Rush  (`scenario_1_peak_rush/`)
> "A normal busy day — but vessels cluster at the gate all at once."

| Field | Value |
|---|---|
| Date | 1 Sep 2025 |
| Vessels | 30 — real shipping line names (MSC, Maersk, CMA CGM, COSCO, ONE…) |
| Berth situation | 4 free, 3 occupied, 1 maintenance |
| Hotspots detected | **2** — 1 × CRITICAL deep water, 1 × MEDIUM general |
| Delayed vessels | 22 |
| Key talking point | Shows how even "normal" port congestion can cascade when vessels bunch at the same window — 7 vessels arrive in 1 hour for only 2.5 effective deep-water berths |

---

### Scenario 2 — Critical Surge  (`scenario_2_critical_surge/`)
> "Emergency — a fleet of high-priority cargo ships all arrive together."

| Field | Value |
|---|---|
| Date | 10 Oct 2025 |
| Vessels | 30 — 8 critical + 8 priority in the first 6 hours |
| Berth situation | 3 free, 2 occupied (not big enough for all), 1 maintenance |
| Hotspots detected | **1 × CRITICAL deep water** (ratio 2.67 — demand nearly 3× supply) |
| Delayed vessels | 23 |
| Key talking point | Demonstrates the priority optimiser protecting all 8 critical vessels (0 min wait) while the queue backs up behind them — exactly what the LA/Long Beach scenario needed |

---

### Scenario 3 — Maintenance Crisis  (`scenario_3_maintenance_crisis/`)
> "Half the port is down for maintenance. Every berth is under pressure."

| Field | Value |
|---|---|
| Date | 20 Nov 2025 |
| Vessels | 30 — 8 critical, spread over a full day |
| Berth situation | **4 berths in maintenance** (C1, C3, C5, C7) — only 4 operational |
| Hotspots detected | **3** — 1 × CRITICAL deep water (ratio 3.0), 1 × HIGH deep water (ratio 1.67), 1 × MEDIUM general |
| Delayed vessels | 26 |
| Key talking point | Most dramatic scenario — shows the system flagging a near-total deep-water capacity collapse and still getting all critical vessels assigned without waiting |
