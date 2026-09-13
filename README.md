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
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/OhmRobin1/bob-ai-hackathon--NullThreat-.git
cd bob-ai-hackathon-nullthreat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run the project
python src/classify_alerts.py
python src/generate_report.py
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

> Be honest — judges appreciate transparency over overclaiming.

- Limitation 1: Uses a simulated alert dataset, not a live SIEM/satellite feed integration
- Limitation 2: MITRE ATT&CK mapping is limited to a predefined reference list of ~10 techniques, not the full framework
- Limitation 3: No persistent database — results are generated per run, not stored historically

---

## 🏅 What We're Most Proud Of

Tell the judges what part of your submission is strongest and worth paying close attention to.

---

