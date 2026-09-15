# Solution Overview

## The Core Mechanism

BLUFShield processes security alerts through a five-stage pipeline:

1. **Ingestion** — Alerts from four source systems (SIEM, Cyber Sensor, Intel Report, Satellite Feed) are read from a unified dataset, each carrying a timestamp, source, severity, and description.
2. **Classification** — Each alert is classified as either a `false_positive` or `real_threat`. In demo mode this runs through a 25-rule keyword engine for instant, offline results; in live mode it's handed to IBM watsonx.ai (Llama-3-70b-Instruct) for zero-shot LLM classification.
3. **MITRE ATT&CK Mapping** — Every confirmed threat is mapped to a specific technique from the MITRE ATT&CK framework (e.g., T1071 C2 Application Layer Protocol, T1041 Exfiltration), grounding the classification in an industry-recognized reference rather than a vague "suspicious" label.
4. **Correlation** — Confirmed threats that share a technique or pattern are grouped into incident clusters, surfacing cases where multiple alerts likely represent stages of the same coordinated attack rather than isolated events.
5. **BLUF Reporting** — Results are synthesized into a Bottom Line Up Front summary: total alerts analyzed, confirmed threat count, highest severity reached, and the most significant correlated cluster — stated immediately, with supporting detail following.

## What Makes This Different from Naive Alternatives

A naive approach to this problem would be a single LLM call that reads a list of alerts and returns a paragraph of "here's what looks suspicious." BLUFShield is deliberately structured differently:

- **Classification and correlation are separate steps**, not one blended output. This means a false positive is never accidentally folded into an incident cluster, and each stage's output can be independently verified — important in a defense context where an analyst needs to trust *why* something was flagged, not just that it was.
- **MITRE ATT&CK mapping is explicit and structured**, not a free-text guess. Every confirmed threat is tied to a specific, real technique ID, which lets an analyst cross-reference against known attacker playbooks rather than taking the model's word for it.
- **Dual classification modes** mean the system doesn't require an API key or internet access to demonstrate its logic — the rule-based demo engine proves the pipeline design works end-to-end, while watsonx.ai mode shows the same pipeline scaling to real LLM-driven classification. This separation also makes the system easier to test and debug, since you can validate pipeline logic offline before trusting it with a live model.

## Key Design Decisions

- **BLUF format was a design requirement, not an afterthought.** The problem statement explicitly calls out that commanders need conclusions in minutes, so the report generator was built around that structure from the start — bottom-line conclusion first, supporting detail after — rather than retrofitting a generic report into BLUF language.
- **Scoped to alert triage and reporting, not live feed ingestion.** Rather than attempting to simulate connections to real SIEM/satellite/sensor APIs (which would be both infeasible to demo credibly and outside the actual problem being solved), BLUFShield works from a realistic simulated dataset. This keeps the focus on the genuinely hard part of the problem —
