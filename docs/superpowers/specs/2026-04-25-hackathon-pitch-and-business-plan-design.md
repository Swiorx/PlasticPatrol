# PlasticPatrol — Hackathon Pitch & Business Plan Design

**Date:** 2026-04-25
**Pitch slot:** 2026-04-26, 15:00 EEST (≈18 hours from spec creation)
**Format:** 3 min pitch + 2 min Q&A
**Challenge addressed:** Protecting Water Resources from Pollution
**Judging weights:** Relevance 33% · Innovativeness 33% · Team 33%
**Hard constraint:** Pre-recorded demo MUST be embedded in submitted slides. Live demos forbidden.

---

## 1. Goals

Produce a complete, judge-ready submission package within 18 hours covering:

1. A 3-minute pitch (script + slide-by-slide deck content).
2. An embedded 30-second demo screencast shot list.
3. A 4-page business plan with B2G + B2B primary revenue and B2C as data-generating moat.
4. A Q&A preparation sheet for the 2-minute Q&A window.

Every artifact maps explicitly to one of the three judging axes.

## 2. Strategic Positioning

**One-line proposition:** *"Copernicus made the data free. PlasticPatrol makes it actionable — the first closed-loop satellite ↔ citizen ↔ satellite verification system for marine plastic cleanup."*

**Defensible moat (innovativeness axis):**
- Custom Sentinel-2 evalscript combining NDWI + FDI + NDVI + SWIR land-kill filters at 10 m.
- ML photo verification (MobileNetV2) at the cleanup site.
- Re-scan satellite confirmation closes the loop — no competitor does this.
- Citizens generate ground-truth verification data for free; institutions pay for that data.

**Regulatory tailwind (relevance + business axis):**
- EU **Packaging & Packaging Waste Regulation (PPWR)** + national **EPR** schemes force plastic producers to fund verified cleanup.
- Coastal municipalities, port authorities, and EMSA need auditable removal data.

## 3. Pitch Architecture (3 minutes / 180 seconds)

| # | Slide | Time (s) | Content summary | Judging axis |
|---|---|---|---|---|
| 1 | Hook + Title | 0–20 | Stat: 11M tonnes/year. "Satellites see it. No one connects them to people who can clean it." | — |
| 2 | The Problem | 20–40 | Detection ≠ cleanup. EU EPR demands *verified* removal. Gap = our wedge. | Relevance |
| 3 | The Solution (architecture diagram) | 40–60 | Sentinel-2 → ML → Citizens → Re-scan verification | Relevance + Innov. |
| 4 | **Embedded demo screencast (30 s)** | 60–95 | Map zoom → cluster → reserve → photo → ML verifies → re-pass → eco-points | Innovation |
| 5 | Why It's Innovative | 95–115 | (1) Custom evalscript at 10 m (2) Closed loop (3) Free citizen ground truth | Innovation |
| 6 | Business Model (flywheel diagram) | 115–145 | Citizens free → verified cleanups → EPR/ESG buyers + B2G institutional buyers pay | Innovation (viability) |
| 7 | Market & Traction | 145–160 | TAM €1.5B EU EPR by 2027. Constanța + Black Sea hotspots already detected. | Innovation |
| 8 | Team (4 photos + 1 line each) | 160–175 | Rares, Matei, Andrei, Swiorx. Tagline: "Built the full stack in 48h." | Team |
| 9 | Ask + Closing | 175–180 | "Copernicus made the data free. We made it actionable." + repo QR | — |

**Speaker:** single speaker recommended for tightness. Backup speaker rehearses identical script.

## 4. Demo Screencast Shot List (30 seconds, embedded in slide 4)

| t (s) | Action | On-screen caption |
|---|---|---|
| 0–4 | Map of Black Sea zooms to Constanța Port; debris clusters (red dots) appear from Sentinel-2 scan | "Sentinel-2 detects floating plastic at 10 m" |
| 4–8 | User clicks a cluster → "Reserve" → 24h lock confirmed | "Citizens reserve a cleanup zone" |
| 8–14 | Photo upload UI; image of beach plastic uploaded; ML returns `{label: debris, confidence: 0.94}` | "ML verifies the photo on-site" |
| 14–22 | Time-skip overlay: "2 days later — Sentinel-2 re-pass". Map shows the cluster removed; toast "Cleanup confirmed +6 eco-points" | "Satellite re-scan confirms removal" |
| 22–30 | Leaderboard fly-in; team name climbs ranks. End card: "PlasticPatrol — space to shore, in one loop." | — |

Recorded via OBS / QuickTime at 1920×1080. No audio (deck plays muted in projector setting); on-screen captions carry the narrative.

## 5. Business Plan Document Structure (~4 pages)

1. **Executive Summary** (½ page) — proposition, market, model, ask.
2. **Problem & Market**
   - 11M tonnes plastic/year into oceans (UNEP).
   - EU PPWR + EPR creates legal demand for verified cleanup data.
   - TAM: €1.5B EU plastic-EPR compliance market by 2027 (cited estimate).
   - SAM: Black Sea + Mediterranean coastal zones, year 1 focus.
3. **Solution & Tech Moat** — closed-loop architecture; custom evalscript; ML; citizen layer.
4. **Business Model (Hybrid: D)**
   - **B2G primary** — SaaS dashboards for ports & coastal municipalities. Pricing: €20k–€80k/year per zone. Buyers: Constanța Port, Galați, Varna, Piraeus, EMSA.
   - **B2B primary** — Verified-cleanup credits for EPR-obligated producers. Pricing: €/kg verified removal (carbon-credit analog). Buyers: Coca-Cola HBC, Nestlé, Unilever, Mars, Romaqua.
   - **B2C secondary (the moat)** — Free citizen app; premium tier €2/month (advanced stats, badges); affiliate eco-products; NGO co-branded campaigns.
   - **Sponsors / Affiliates** — Branded cleanup zones ("Coca-Cola Black Sea Zone"); affiliate commerce on reusable goods; EU Horizon Europe grants; ESA BIC incubation.
5. **Go-to-Market**
   - Y1: Constanța Port pilot + 1 corporate sponsor (target: Coca-Cola HBC Romania) + EU Horizon application.
   - Y2: Black Sea regional rollout (Romania, Bulgaria, Turkey) + 3–5 corporate sponsors.
   - Y3: EU coastal expansion (Mediterranean, Adriatic).
6. **Competitive Landscape** — Plastic Pirates (citizen-only, no satellite), The Ocean Cleanup (capture-only, no verification platform), OceanScan / Marine Litter Watch (detection-only, no closed loop). PlasticPatrol = only closed loop.
7. **Financial Projection (lightweight, 3-year)**
   - Y1 revenue €50k (1 pilot + 1 sponsor + grant).
   - Y2 €400k (4 zones + 3 sponsors).
   - Y3 €1.8M (15 zones + 8 sponsors + premium tier scale).
   - Costs dominated by satellite API quota, dev team, BD; gross margin ~70% by Y3.
8. **Team & Ask**
   - Team bios with role + relevant expertise.
   - Ask: pilot partner introductions (ports, EMSA), €150k seed/grant, mentorship on EPR compliance sales.

## 6. Q&A Preparation (anticipated questions)

Prepared 30-second answers for:
1. Sentinel-2 revisit cadence vs cleanup confirmation latency (answer: 2–5 days; we surface "awaiting verification" state).
2. ML false-positive rate and dataset size (answer: MobileNetV2 baseline; expansion via citizen-uploaded labelled data flywheel).
3. Why won't a port just hire a boat instead? (answer: scale + auditability — no boat surveys 12 km radius daily for €).
4. EPR compliance specifics — how is "verified cleanup" recognised legally? (answer: emerging space; we sell auditable records as input to compliance reports, not legal certification — yet).
5. Privacy / GPS handling for citizens (answer: opt-in location, GDPR-compliant, no third-party sharing).
6. Scaling beyond EU (answer: same regulatory wave in UK, Canada, Australia; data product is jurisdiction-agnostic).
7. Unit economics per cleanup (answer: €/kg credit price > marginal ML+API cost; flywheel improves with scale).
8. Defensibility against a copycat (answer: dataset moat from citizen verifications + first-mover EPR partnerships).

## 7. Deliverables

All produced as Markdown in `docs/superpowers/specs/` or repo root, ready to be pasted into Google Slides / a Google Doc by a human within 18 hours.

| File | Purpose |
|---|---|
| `PITCH_SCRIPT.md` | Word-for-word 3-min script (~480 words), timing-marked. |
| `SLIDE_DECK_OUTLINE.md` | Slide-by-slide content + visuals + layout notes. |
| `DEMO_SCREENCAST_SHOTLIST.md` | Exact 30 s shot list with on-screen captions. |
| `BUSINESS_PLAN.md` | 4-page business plan (sections in §5). |
| `QA_PREP.md` | 8 anticipated Q&A pairs (§6). |

## 8. Out of Scope

- Visual design of the actual deck (slides assembled by team in Google Slides).
- Recording the screencast video (team records using shot list).
- Logo/branding redesign.
- Detailed financial model spreadsheet (lightweight projection only).
- Code changes to the application.

## 9. Acceptance Criteria

- [ ] Pitch script reads aloud in 175–180 s at conversational pace.
- [ ] Every slide explicitly serves at least one judging axis (mapped in §3).
- [ ] Demo screencast shot list ≤ 30 s with captions.
- [ ] Business plan covers all 8 sections in §5, names specific target buyers/sponsors.
- [ ] Q&A sheet has prepared answers for the 8 questions in §6.
- [ ] All deliverables ready for human review ≥ 12 hours before pitch slot.
