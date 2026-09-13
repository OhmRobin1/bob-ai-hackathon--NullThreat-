# 🚀 Threat Intelligence Correlation & Alert Prioritization


---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | NullThreat |
| **Track** | AI |
| **Team Lead** | Bhargav — [email@ibm.com] |
| **Members** | Saumya, Milonee, Ohm |

---

## 🎯 Problem Statement

Defense analysts receive thousands of security alerts daily from SIEM systems, satellite feeds, and cyber sensors, in inconsistent formats — no human team can review them all manually. Missing a genuine threat is catastrophic, while chasing false positives wastes critical response time, and commanders need clear, prioritized threat summaries in minutes, not hours.

---

## 💡 Solution

NullThreat is an AI-powered alert triage tool that ingests security alerts, uses an LLM to classify each as a false positive or genuine threat, maps real threats to known MITRE ATT&CK techniques, and generates a BLUF (Bottom Line Up Front) summary report so analysts can act on the highest-priority threats first.

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
| **Frameworks** | None - command-line scripts only |
| **IBM Technologies** | IBM Bob, watsonx.ai |
| **Databases** | None - alerts and results stored as CSV files |
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

git clone https://github.com/OhmRobin1/bob-ai-hackathon-nullthreat.git
cd bob-ai-hackathon-nullthreat

pip install -r requirements.txt

cp .env.example .env
# Add your watsonx/API key to .env

python src/classify_alerts.py
python src/generate_report.py
```bash
# 1. Clone the repo
git clone https://github.com/[your-repo].git
cd [your-repo]

# 2. Install dependencies
[your install command here]

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run the project
[your run command here]
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

- [Limitation 1: Uses a simulated alert dataset, not a live SIEM/satellite feed integration]
- [Limitation 2: MITRE ATT&CK mapping is limited to a predefined reference list of ~10 techniques, not the full framework]
- [Limitation 3: No persistent database — results are generated per run, not stored historically]

---

## 🏅 What We're Most Proud Of

[Tell the judges what part of your submission is strongest and worth paying close attention to.]

---
