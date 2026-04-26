# Hackathon Pitch & Business Plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce 5 judge-ready Markdown deliverables for the Copernicus hackathon pitch (Protecting Water Resources from Pollution challenge), inside a dedicated folder, within 18 hours.

**Architecture:** All deliverables are Markdown documents written into `pitch/` at the repo root. Each file is independent — no cross-imports — but they cross-reference each other (script ↔ slides ↔ shotlist). The spec at `docs/superpowers/specs/2026-04-25-hackathon-pitch-and-business-plan-design.md` is the source of truth for content, timing, and named entities.

**Tech Stack:** Markdown only. No code, no tests in the conventional sense. "Verification" = read-aloud timing, word-count, and section-coverage checks.

---

## File Structure

All deliverables live in a new folder `pitch/` at the repo root (per user request: "create a separate folder for these inside the directory").

```
pitch/
├── README.md                      # 1-page index pointing to each artifact + how to use
├── PITCH_SCRIPT.md                # Word-for-word 3-min script, timing-marked
├── SLIDE_DECK_OUTLINE.md          # 9 slides with content + visual notes
├── DEMO_SCREENCAST_SHOTLIST.md    # 30s shot list with on-screen captions
├── BUSINESS_PLAN.md               # 4-page business plan
└── QA_PREP.md                     # 8 anticipated Q&A pairs
```

Source-of-truth spec: `docs/superpowers/specs/2026-04-25-hackathon-pitch-and-business-plan-design.md`.

---

## Task 0: Create `pitch/` folder and README index

**Goal:** Create the deliverables folder and a 1-page index README so the team can navigate the package.

**Files:**
- Create: `pitch/README.md`

**Acceptance Criteria:**
- [ ] `pitch/` directory exists at repo root
- [ ] `pitch/README.md` lists all 5 deliverables, what each is for, recommended reading order, and pitch-day checklist

**Verify:** `ls pitch/ && head -40 pitch/README.md` → folder exists, README lists 5 files

**Steps:**

- [ ] **Step 1:** Create the folder via `mkdir -p pitch`
- [ ] **Step 2:** Write `pitch/README.md` with sections:
  - **What's in this folder** — bullet list of 5 files with one-line purpose each
  - **Reading order for the team** — Script → Slides outline → Shotlist → Business plan → Q&A prep
  - **Pitch-day checklist** — slides built from outline, screencast recorded from shotlist, script rehearsed to 175–180s, business plan exported as PDF, Q&A sheet printed
  - **Hard constraints** — 3 min hard cap, demo MUST be embedded in slides, live demos forbidden
- [ ] **Step 3:** Commit
  ```bash
  git add pitch/README.md
  git commit -m "pitch: add deliverables folder and index"
  ```

---

## Task 1: Write `pitch/PITCH_SCRIPT.md`

**Goal:** Word-for-word 3-min speaker script, timing-marked per slide, ~480 words.

**Files:**
- Create: `pitch/PITCH_SCRIPT.md`

**Acceptance Criteria:**
- [ ] Script broken into 9 timed blocks matching spec §3 slide timings (20+20+20+35+20+30+15+15+5 = 180 s)
- [ ] Total word count 460–500 (≈2.7 words/sec sustainable speaking pace)
- [ ] Each block has timing header (e.g., `### [0:00–0:20] Slide 1 — Hook`)
- [ ] Single-speaker, conversational, no jargon dump
- [ ] Closing line matches spec: "Copernicus made the data free. We made it actionable."
- [ ] Notes at top: rehearsal instructions, where to pause for demo video, fallback if running long

**Verify:** `wc -w pitch/PITCH_SCRIPT.md` → 460–500 words in script body (excluding headings/notes)

**Steps:**

- [ ] **Step 1:** Read spec §3 (slide architecture) to anchor each timed block
- [ ] **Step 2:** Draft script block-by-block, using the "Hook → Problem → Solution → Demo (silent) → Why innovative → Business model → Market → Team → Ask" arc. During the 35s demo block, the speaker narrates over the muted screencast (captions on screen carry the literal words, speaker adds context).
- [ ] **Step 3:** Word-count check; trim/pad to 460–500
- [ ] **Step 4:** Add top-of-file rehearsal notes (speak slowly through the hook, accelerate through tech, slow again at the ask)
- [ ] **Step 5:** Commit
  ```bash
  git add pitch/PITCH_SCRIPT.md
  git commit -m "pitch: add 3-minute speaker script"
  ```

---

## Task 2: Write `pitch/SLIDE_DECK_OUTLINE.md`

**Goal:** Slide-by-slide content document — every slide has headline, body text, visual element, layout notes — ready to paste into Google Slides.

**Files:**
- Create: `pitch/SLIDE_DECK_OUTLINE.md`

**Acceptance Criteria:**
- [ ] 9 slides matching spec §3 table
- [ ] Each slide block contains: `Headline`, `Body` (≤ 25 words), `Visual` (what image/diagram), `Layout` (e.g., "centered", "split 60/40 left text right diagram"), `Speaker reference` (cross-link to script block)
- [ ] Slide 4 explicitly notes: embed `screencast.mp4` (autoplay on slide enter, muted, looped if needed)
- [ ] Slide 6 (business model) describes the flywheel diagram in enough detail that a designer can draw it
- [ ] Slide 8 (team) specifies 4 photo placeholders + 1-line bios from spec

**Verify:** `grep -c "^## Slide" pitch/SLIDE_DECK_OUTLINE.md` → 9

**Steps:**

- [ ] **Step 1:** Write file scaffold with 9 `## Slide N — Title` sections
- [ ] **Step 2:** For each slide, fill in 5 fields (Headline, Body, Visual, Layout, Speaker reference)
- [ ] **Step 3:** Add header note: visual style guidance (dark blue + Copernicus orange palette, sans-serif, minimal text per slide), and tooling note (Google Slides recommended for collaborative speed)
- [ ] **Step 4:** Add footer note: pre-pitch tech check (autoplay enabled, video file embedded not linked, presenter view tested)
- [ ] **Step 5:** Commit
  ```bash
  git add pitch/SLIDE_DECK_OUTLINE.md
  git commit -m "pitch: add slide-by-slide deck outline"
  ```

---

## Task 3: Write `pitch/DEMO_SCREENCAST_SHOTLIST.md`

**Goal:** Exact 30-second screencast shot list with on-screen captions, recording settings, and software guidance.

**Files:**
- Create: `pitch/DEMO_SCREENCAST_SHOTLIST.md`

**Acceptance Criteria:**
- [ ] 5 shot blocks per spec §4 covering: detection, reservation, photo verification, satellite re-pass, leaderboard
- [ ] Total runtime ≤ 30 seconds; cumulative timestamps per shot
- [ ] On-screen caption text quoted verbatim per shot
- [ ] Recording specs section: 1920×1080, 30fps, MP4 H.264, no audio, OBS or QuickTime
- [ ] Pre-recording checklist: seed data loaded, browser zoom 100%, mock satellite pass enabled if 2-day wait infeasible
- [ ] Failure modes & fallbacks: what to do if ML returns "clean" unexpectedly, if satellite re-pass not yet available

**Verify:** `grep -c "^### Shot" pitch/DEMO_SCREENCAST_SHOTLIST.md` → 5

**Steps:**

- [ ] **Step 1:** Write 5 `### Shot N (t=A–B s)` blocks copying timing from spec §4
- [ ] **Step 2:** For each shot list: action description, mouse movements, on-screen caption text, expected backend response
- [ ] **Step 3:** Add Recording Specs and Pre-Recording Checklist sections
- [ ] **Step 4:** Add Failure-Mode section addressing satellite-pass latency (instruct: use seeded "confirmed" cluster; or use mock satellite endpoint for the demo only)
- [ ] **Step 5:** Commit
  ```bash
  git add pitch/DEMO_SCREENCAST_SHOTLIST.md
  git commit -m "pitch: add 30s demo screencast shot list"
  ```

---

## Task 4: Write `pitch/BUSINESS_PLAN.md`

**Goal:** 4-page business plan covering hybrid B2G + B2B + B2C model with named buyers, sponsors, EU regulation citations, and 3-year financial projection.

**Files:**
- Create: `pitch/BUSINESS_PLAN.md`

**Acceptance Criteria:**
- [ ] 8 sections per spec §5: Executive Summary, Problem & Market, Solution & Tech Moat, Business Model, Go-to-Market, Competitive Landscape, Financial Projection, Team & Ask
- [ ] EU PPWR + EPR cited explicitly with what they require
- [ ] Named B2G targets: Constanța Port, Galați, Varna, Piraeus, EMSA
- [ ] Named B2B sponsor candidates: Coca-Cola HBC, Nestlé, Unilever, Mars, Romaqua
- [ ] 3-year revenue table: Y1 €50k, Y2 €400k, Y3 €1.8M, with 1-line driver each
- [ ] Affiliates / sponsorship section: branded zones, eco-product affiliates, NGO co-branding (Plastic Soup Foundation, WWF, Ocean Conservancy)
- [ ] Funding ask: €150k seed/grant + pilot partner intros + EPR sales mentorship
- [ ] Length: target 1500–2200 words (≈4 printed pages)

**Verify:** `wc -w pitch/BUSINESS_PLAN.md` → 1500–2200

**Steps:**

- [ ] **Step 1:** Outline 8 section headings
- [ ] **Step 2:** Write Executive Summary last; draft sections 2–8 first
- [ ] **Step 3:** Insert revenue table as Markdown table in §7
- [ ] **Step 4:** Add a competitive-landscape table comparing PlasticPatrol vs Plastic Pirates / The Ocean Cleanup / OceanScan on 4 axes (detection, verification, citizen engagement, closed loop)
- [ ] **Step 5:** Word-count check; trim/pad to 1500–2200
- [ ] **Step 6:** Commit
  ```bash
  git add pitch/BUSINESS_PLAN.md
  git commit -m "pitch: add 4-page business plan"
  ```

---

## Task 5: Write `pitch/QA_PREP.md`

**Goal:** 8 anticipated questions, each with a 30-second prepared answer (~75 words).

**Files:**
- Create: `pitch/QA_PREP.md`

**Acceptance Criteria:**
- [ ] 8 Q/A pairs from spec §6
- [ ] Each answer 60–90 words (deliverable in ~30 s)
- [ ] Q&A on: revisit cadence latency, ML false positives, port-buys-boat-instead, EPR legal recognition, GDPR/privacy, scaling beyond EU, unit economics, defensibility
- [ ] Top-of-file note on the 2-min Q&A budget: prioritize relevance/innovation/team angles in answers

**Verify:** `grep -c "^### Q[0-9]" pitch/QA_PREP.md` → 8

**Steps:**

- [ ] **Step 1:** Write 8 `### Q1` … `### Q8` blocks with the question text from spec §6
- [ ] **Step 2:** Under each, write a `**Answer:**` of 60–90 words
- [ ] **Step 3:** Add header note on tone (confident, brief, redirect to the moat) and a "ban list" of words/phrases to avoid (e.g., "we hope to", "in theory")
- [ ] **Step 4:** Commit
  ```bash
  git add pitch/QA_PREP.md
  git commit -m "pitch: add Q&A preparation sheet"
  ```

---

## Self-Review

- **Spec coverage:** Spec §3 (pitch architecture) → Tasks 1, 2. §4 (shot list) → Task 3. §5 (business plan) → Task 4. §6 (Q&A) → Task 5. §7 (deliverables list) → all tasks + Task 0. §8 (out of scope) respected: no slide visuals, no actual recording, no logo/branding.
- **Placeholders:** None — every task has explicit acceptance criteria and verification commands.
- **Type/name consistency:** File names match spec §7 verbatim; counts (8 Q&A, 9 slides, 5 shots) consistent across plan and spec.
- **Folder request:** Task 0 creates `pitch/` per user instruction.

Plan is consistent and complete.
