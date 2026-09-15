# 🚀 BLUFSheild

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | NullThreat |
| **Track** | AI |
| **Team Lead** | Bhargav — bhargavjagtap640@gmail.com |
| **Members** | Milonee, Saumya, Ohm |

---

## 🎯 Problem Statement

<small> Defense analysts receive thousands of security alerts daily from SIEM systems, satellite feeds, and cyber sensors, in inconsistent formats — no human team can review them all manually. Missing a genuine threat is catastrophic, while chasing false positives wastes critical response time, and commanders need clear, prioritized threat summaries in minutes, not hours. </small>
---

## 💡 Solution

<small> BLUFShield ingests security alerts from multiple source systems and classifies each as a false positive or confirmed threat, maps confirmed threats to MITRE ATT&CK techniques, groups correlated alerts into incident clusters, and generates a BLUF (Bottom Line Up Front) summary so analysts can act on the highest-priority threats first. It runs in two modes: an offline rule-based demo classifier for instant results, and a live watsonx.ai (Llama-3-70b-Instruct) mode for real LLM-driven classification. </small>
---

## ✨ Key Features

- **Alert Classification:** 40 ingested alerts triaged into confirmed threats vs. false positives, with a live signal-to-noise breakdown
- **MITRE ATT&CK Mapping:** Confirmed threats mapped across 10 ATT&CK techniques (e.g., T1071 C2 Protocol, T1041 Exfiltration, T1190 Exploit App), with a clickable technique matrix
- **Incident Correlation:** Related alerts grouped into incident clusters by shared technique, surfacing multi-alert attack chains
- **BLUF Summary Report:** Auto-generated Bottom Line Up Front report highlighting confirmed threat count, severity, and the most significant correlated cluster
- **Interactive Live Demo:** Paste or type any alert description in-browser and get an instant classification, with sample alerts and analysis history
- **Dual Classification Modes:** Offline 25-rule keyword engine by default; switches to IBM watsonx.ai for real zero-shot LLM classification via `CLASSIFY_MODE=watsonx`

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** |  Python, JavaScript, HTML/CSS |
| **Frameworks** | None — static dashboard + Python scripts |
| **IBM Technologies** | IBM Bob, IBM watsonx.ai (Llama-3-70b-Instruct) |
| **Databases** | None — alerts and results stored as CSV/JSON files |
| **Other** | GitHub Pages (live demo hosting), GitHub Actions (template validation) |

---

## 📁 Repository Structure

```
├── src/ # All source code
│ ├── data/ # alerts.csv (40 simulated alerts, 4 source systems)
│ ├── classify_alerts.py
│ ├── generate_report.py
│ └── output/ # results.json, bluf_report.md
├── docs/ # Written documentation
│ ├── problem-statement.md
│ ├── solution-overview.md
│ ├── architecture.md
│ └── setup-guide.md
├── demo/ # Demo artifacts
│ ├── screenshots/ # App screenshots
│ └── demo-video-link.txt # Link to demo video
├── presentation/ # Slide deck
└── submission.yaml # Structured submission metadata
```

---

## ⚡ How to Run

```bash
# 1. Clone the repo
git clone https://github.com/ohmrobin1/bob-ai-hackathon--NullThreat-.git
cd bob-ai-hackathon--NullThreat-

# 2. Install dependencies
pip install -r requirements.txt

# 3. Classify alerts (demo mode — no API key needed)
python src/classify_alerts.py

# 4. Generate the BLUF report
python src/generate_report.py

# Optional: switch to live watsonx.ai classification
# Add WATSONX_API_KEY + WATSONX_PROJECT_ID to src/.env, then:
CLASSIFY_MODE=watsonx python src/classify_alerts.py
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 🔗 Live Dashboard | [BLUFShield Live Demo](https://ohmrobin1.github.io/bob-ai-hackathon--NullThreat-/) |
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

- Uses a simulated 40-alert dataset, not a live SIEM/satellite feed integration
- Demo mode classification uses a 25-rule keyword engine, not the LLM — watsonx.ai mode requires an API key to activate real zero-shot classification
- MITRE ATT&CK mapping is limited to 10 predefined techniques, not the full framework
- No persistent database — results are generated per run, not stored historically across sessions
---

## 🏅 What We're Most Proud Of

We're proud that BLUFShield doesn't just classify alerts — it correlates them into incident clusters and grounds every confirmed threat in a real MITRE ATT&CK technique, giving analysts a framework-based starting point instead of a vague flag. We also built a genuinely interactive live demo where anyone can paste an alert and see the classification pipeline work in real time, rather than just showing static screenshots of output.

---
