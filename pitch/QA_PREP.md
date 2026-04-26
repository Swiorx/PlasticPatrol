# Q&A Preparation Sheet — PlasticPatrol Copernicus Hackathon

## Q&A strategy

- **2-minute total budget — ≤ 30 seconds per answer (~75 words).** Stop when the point is made. Over-answering kills time and signals nerves.
- **Answer to the room, not to the questioner.** Acknowledge the judge who asked, then sweep eye contact across the full panel.
- **Off-sheet question template:** (1) One-sentence acknowledgement of the question. (2) One-sentence pivot to the closest moat angle — relevance, innovation, or team. (3) One concrete fact that grounds the answer.
- **Ban list — phrases NOT to use:** "we hope to", "in theory", "potentially", "we believe", "we think", "kind of", "sort of", "I'm not sure but". Replace every hedged phrase with a declarative statement or "we don't know yet — here's what we'd need to find out".
- **Designated answerers — decide before you walk on stage:** route business questions (Q3, Q4, Q7) to the team member most fluent on regulation and business model; route technical questions (Q1, Q2, Q5, Q8) to the appropriate engineering lead.

---

### Q1 — Sentinel-2 revisit cadence

"Sentinel-2 has a ~5-day revisit time. How can you confirm a cleanup quickly enough for the user experience to feel responsive?"

**Answer:** The 2–5 day re-pass window is honest and we design around it. The moment a user submits a cleanup, the app surfaces an "awaiting verification" state with a live countdown to the next satellite pass — progress is visible immediately. Eco-points are awarded on confirmed re-pass. Speed is not our differentiator; auditability is. That verified, timestamped satellite record is exactly what EPR buyers pay for, and a same-day photo alone cannot provide it.

---

### Q2 — ML false positives

"What's your classifier's accuracy and how do you handle false positives?"

**Answer:** We use MobileNetV2 trained on labelled ocean debris imagery. Every citizen-uploaded photo feeds a continuous retraining pipeline — the dataset moat compounds with each cleanup. The model exposes a confidence score; submissions below threshold go to human review rather than auto-rejection. Critically, final verification is multi-stage: photo classification plus independent satellite re-pass confirmation. A false positive at either single stage does not corrupt the audit record, because both signals must agree.

---

### Q3 — Why not just hire a boat?

"Why would a port pay for this when they could just send a boat to inspect?"

**Answer:** A survey vessel cannot cover a 12 km radius continuously, and it produces no machine-readable record a port can submit to regulators. PlasticPatrol delivers persistent monitoring at a fraction of the operational cost, and outputs structured, timestamped audit data aligned to EU reporting requirements. We complement boats — when a hotspot is confirmed by satellite, a targeted vessel deployment becomes far more cost-effective. The question isn't boat versus satellite; it's unstructured patrols versus auditable continuous intelligence.

---

### Q4 — EPR legal recognition

"Is your verified-cleanup record legally recognised as EPR compliance evidence?"

**Answer:** This is an emerging regulatory space and we are transparent about that. We do not claim to issue legal certifications today. We sell the auditable underlying record — satellite imagery, ML verification, GPS coordinates, and timestamp — as structured input to the compliance reports producers file with EPR authorities. We are already engaging with regulators to shape how this class of verified evidence is treated under the PPWR framework, and that engagement is itself a first-mover advantage.

---

### Q5 — GDPR / privacy

"You're tracking citizens' GPS locations. How is that GDPR-compliant?"

**Answer:** Location data is collected only on explicit opt-in, and only when a user actively reserves a debris cluster or uploads a cleanup photo — never passively. Data is stored encrypted, retained solely for the verification window of that specific cleanup, and never shared with third parties. Users can delete their account and all associated data at any time. This is a standard EU privacy-by-design pattern: data minimisation, purpose limitation, and full user control, built in from day one.

---

### Q6 — Scaling beyond EU

"Your moat is EU regulation. What happens outside Europe?"

**Answer:** The same regulatory wave is active globally. The UK, Canada, Australia, and several US states already have plastic-EPR schemes in force or moving through legislation. Singapore and Japan are advancing comparable frameworks in Asia-Pacific. Our satellite and ML infrastructure is entirely jurisdiction-agnostic. We focus on the EU first because the regulation is most mature and the buyers are most defined, but the identical pipeline — detect, verify, certify — deploys to any coastline without architectural change.

---

### Q7 — Unit economics

"What's the unit economics on a single cleanup?"

**Answer:** Marginal cost per verified cleanup is Sentinel API quota, ML inference, and a fraction of citizen-app server costs — low single-digit cents per event. Revenue is priced per kilogram of verified removal at €0.50–€2.00; typical cluster removals cover multiple kilograms. That gives a strong contribution margin even at early scale. We model gross margin scaling toward 70% by year 3 as the citizen network grows, fixed infrastructure costs amortise, and higher-value institutional contracts replace pilot-tier pricing.

---

### Q8 — Defensibility against copycats

"Sentinel-2 data is free. What stops a competitor from copying you in 6 months?"

**Answer:** Three compounding moat layers. First, custom evalscript tuning — calibrating NDWI, FDI, NDVI, and SWIR thresholds to minimise false positives in real coastal conditions is non-trivial; getting it wrong makes the product unsellable. Second, network flywheel: more citizen cleanups generate more training data, which improves ML accuracy, which attracts more institutional buyers — that loop is already spinning. Third, first-mover EPR partnerships lock in reference customers that make winning the next contract structurally easier. The satellite data is free; the verified, audit-ready output is not replicable overnight.
