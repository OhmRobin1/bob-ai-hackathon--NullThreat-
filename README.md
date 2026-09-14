# 🚀 Threat Intelligence Correlation & Alert Prioritisation Assistant


---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | NullThreat |
| **Track** | AI |
| **Team Lead** | Bhargav Paragkumar Jagtap — 26cs031@charusat.edu.in |
| **Members** | Milonee Shah, Saumya Jain, Ohm Soman |

---

## 🎯 Problem Statement

> In 2–3 sentences: What problem does your project solve? Who experiences this problem?

Defence analysts face thousands of alerts from different sources,
making it difficult to identify genuine threats while filtering out false positives.
The solution prioritizes critical threats and generate clear BLUF (Bottom Line Up Front)
summaries so commanders can quickly understand the situation and take action.

---

## 💡 Solution

> In 2–3 sentences: What did you build? How does it solve the problem above?

The solution prioritizes genuine and critical threats while filtering out false positives from thousands of alerts. It generates clear BLUF summaries to help commanders quickly understand threats and make informed decisions.

---

## ✨ Key Features

- **Feature 1:** Automated alert classification (false positive vs. real threat) using LLM analysis
- **Feature 2:** MITRE ATT&CK technique mapping for confirmed threats
- **Feature 3:** Correlated grouping of related alerts into single incidents
- **Feature 4:** Auto-generated BLUF-style threat summary report

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python |
| **Frameworks** | None — command-line scripts only |
| **IBM Technologies** | IBM Bob, watsonx.ai |
| **Databases** | alerts and results stored as CSV/JSON files|
| **Other** | GitHub Actions |

---

## 📁 Repository Structure

```
├── src/                        # All source code
│   ├── classify_alerts.py      # Step 1: AI alert classifier (demo + watsonx.ai modes)
│   ├── generate_report.py      # Step 2: BLUF report generator
│   ├── requirements.txt        # Python dependencies
│   ├── data/alerts.csv         # 40 simulated security alerts (input)
│   └── output/                 # Generated outputs (results.json, bluf_report.md)
├── demo/                       # Demo dashboard
│   └── index.html              # ← Open this in any browser to see the full demo
├── docs/                       # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── presentation/               # Slide deck
└── submission.yaml             # Structured submission metadata
```

---

## ⚡ How to Run

### Option A — View Demo (no install needed)
```
1. Clone the repo
2. Open  demo/index.html  in any browser
3. Done — no server, no Python, no API key required
```

### Option B — Run the full Python pipeline
```bash
# 1. Clone the repo
git clone https://github.com/OhmRobin1/bob-ai-hackathon--NullThreat-.git
cd bob-ai-hackathon--NullThreat-

# 2. Install dependencies
pip install -r src/requirements.txt

# 3. Run the classifier (demo mode — no API key needed)
python src/classify_alerts.py

# 4. Generate the BLUF report
python src/generate_report.py

# 5. (Optional) Switch to IBM watsonx.ai mode
# Copy src/.env.example to src/.env, fill in WATSONX_API_KEY + WATSONX_PROJECT_ID
# Then: set CLASSIFY_MODE=watsonx and re-run classify_alerts.py
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 🌐 **Interactive Dashboard** | **[Open demo/index.html](demo/index.html)** — open in any browser, no install needed |
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

> **Demo highlights:** Dashboard · All Alerts (filterable/sortable) · Incident Groups · MITRE ATT&CK Matrix · 🧪 Live Classifier (type any alert, get instant classification + MITRE mapping)

---

## ⚠️ Known Limitations

> Be honest — judges appreciate transparency over overclaiming.

- Limitation 1: Uses a simulated alert dataset, not a live SIEM/satellite feed integration
- Limitation 2: MITRE ATT&CK mapping is limited to a predefined reference list of ~10 techniques, not the full framework
- Limitation 3: No persistent database — results are generated per run, not stored historically

---

## 🏅 What We're Most Proud Of

As first-year students building our first real project from scratch, we're proud that every one of us — regardless of prior coding experience — understands how BLUFShield works end-to-end and can explain any part of it. We used IBM Bob not just to generate code, but as a genuine learning partner throughout the build.

---

