# PlasticPatrol — Slide Deck Outline
**Hackathon: Copernicus — Protecting Water Resources from Pollution**
**Format: 3-minute pitch + 2-minute Q&A | 9 slides**

---

## Visual style guidance

- **Palette:** Deep navy blue (#0B2545) primary, Copernicus orange (#F97316) accent, white text. Avoid pure black backgrounds.
- **Font:** Sans-serif (Inter, Roboto, or whatever the team has). Headlines 48–60pt, body 24–28pt.
- **One idea per slide.** If a sentence won't fit in 25 words, cut it.
- **Tooling recommendation:** Google Slides for collaborative editing speed.

---

## Slide 1 — Hook + Title

- **Headline:** "11 million tonnes. One ocean. Zero verification."
- **Body:** PlasticPatrol — Space-to-shore plastic cleanup, verified.
- **Visual:** Full-bleed dark photo of plastic-choked ocean water. PlasticPatrol logo positioned bottom-right. Small Copernicus logo positioned bottom-left. Slight dark vignette overlay so white headline text is legible.
- **Layout:** Centered headline over full-bleed background image. Logos pinned to bottom corners. No extra clutter.
- **Speaker reference:** See PITCH_SCRIPT.md → [0:00–0:20]

---

## Slide 2 — The Problem

- **Headline:** "Detection ≠ cleanup."
- **Body:** EU PPWR & EPR demand verified plastic removal. No tool closes the loop from space to ground to audit.
- **Visual:** Three line icons in a horizontal row with connecting arrows. Icon 1: satellite dish (labeled "Detects — yes"). Icon 2: broom/cleanup (labeled "Removed — unverified?"). Icon 3: clipboard/audit (labeled "Proof — missing"). Use simple monochrome line icons; no emoji. The gap between icon 2 and icon 3 is visually emphasized (broken arrow or red X).
- **Layout:** Headline top-center. Icons row centered vertically below headline. Each icon has a short label underneath. Navy background, white text, orange accent on the broken link.
- **Speaker reference:** See PITCH_SCRIPT.md → [0:20–0:40]

---

## Slide 3 — The Solution

- **Headline:** "From orbit to action — and back."
- **Body:** Sentinel-2 detects → Citizens clean → Satellite re-pass verifies → EPR-compliant proof.
- **Visual:** Architecture diagram: four rectangular boxes arranged in a closed loop (top → right → bottom → left). Box 1 (top): Sentinel-2 satellite icon, label "Detect". Box 2 (right): Chip/ML icon, label "Classify". Box 3 (bottom): Person with smartphone icon, label "Clean". Box 4 (left): Re-scan arrow icon, label "Verify & Audit". Curved arrows connect each box clockwise. An additional return arrow from Box 4 back to Box 1 closes the loop and is highlighted in Copernicus orange.
- **Layout:** 60/40 split — headline and one-line body left; closed-loop diagram right. Navy background.
- **Speaker reference:** See PITCH_SCRIPT.md → [0:40–1:00]

---

## Slide 4 — Live in 30 seconds (DEMO)

- **Headline:** "See it work."
- **Body:** *(no body text — video fills the slide)*
- **Visual:** Embedded video file `screencast.mp4`. Autoplay on slide enter, muted, no playback controls visible, sized 1920×1080. The video must be embedded as a file (not linked) so it plays without an internet connection. A thin Copernicus-orange border frames the video.
- **Layout:** Headline in small text at the very top (24pt). Video occupies the full remaining slide area below the headline. No other elements.
- **Speaker reference:** See PITCH_SCRIPT.md → [1:00–1:35]

---

## Slide 5 — Why It's Innovative

- **Headline:** "Three things nobody else does."
- **Body:** 1. Custom Sentinel-2 evalscript at 10 m. 2. Closed-loop verification — first of its kind. 3. Citizens generate free ground-truth data.
- **Visual:** Three equal vertical columns, each with a single large bold icon at top and a one-line caption below. Column 1: satellite/signal icon — "10 m Sentinel-2 evalscript (NDWI + FDI + NDVI + SWIR)". Column 2: loop/cycle icon — "Closed-loop, end-to-end verification". Column 3: crowd/people icon — "Citizens as free ground-truth sensors". Use the project's navy/orange palette; icon fill in orange, captions in white.
- **Layout:** Headline top-center. Three columns fill the lower 70% of the slide equally. Navy background.
- **Speaker reference:** See PITCH_SCRIPT.md → [1:35–1:55]

---

## Slide 6 — Business Model

- **Headline:** "A flywheel powered by EU regulation."
- **Body:** Citizens (free) → verified cleanups → EPR credits (€/kg) sold to producers + SaaS dashboards sold to ports & EMSA.
- **Visual:** Flywheel diagram: four circular nodes arranged in a clockwise cycle with bold arrows between them. Node A (top): "Citizens (free)". Node B (right): "Verified Cleanups". Node C (bottom): "EPR Credits — Coca-Cola, Nestlé, Unilever (€/kg)". Node D (left): "Dashboards — Constanța Port, EMSA (€20–80k/yr)". Each arrow is labeled with the value transfer (e.g., "generate", "unlock", "fund"). Use alternating navy/orange fills on nodes.
- **Layout:** Headline top-center. Flywheel diagram centered and large, occupying the lower 65% of the slide.
- **Speaker reference:** See PITCH_SCRIPT.md → [1:55–2:25]

---

## Slide 7 — Market & Traction

- **Headline:** "€1.5B by 2027. We start in the Black Sea."
- **Body:** EU plastic-EPR compliance market: €1.5B by 2027. Pilot-ready in Constanța Port. Hotspots detected: Bosphorus, Rotterdam, Singapore Strait.
- **Visual:** Map of Europe, the Mediterranean, and nearby seas. Red pulsing-dot markers on key hotspot locations: Constanța (Black Sea), Bosphorus, Rotterdam (North Sea), Strait of Malta, Singapore Strait (inset or label). Title overlay banner across the top of the map: "TAM €1.5B · Pilot zone: Constanța". Map uses a dark ocean-chart style consistent with navy palette; land masses in muted grey.
- **Layout:** Headline top-center. Map fills 75% of the slide. Stats callout in a small orange box bottom-left.
- **Speaker reference:** See PITCH_SCRIPT.md → [2:25–2:40]

---

## Slide 8 — Team

- **Headline:** "The team that built the loop."
- **Body:** *(no body text — bios embedded in visual)*
- **Visual:** Four equal circular photo placeholders in a horizontal row. Underneath each circle: name in bold white, then role in smaller orange text. Left to right: (1) Rares Neacsu — Satellite & Backend lead. (2) Matei Necula — Full-stack & ML. (3) Andrei Stan — Frontend & Maps. (4) Swiorx — Backend & API. Below the row, centered: "Built the full stack in 48 hours." in italic white 24pt.
- **Layout:** Headline top-center. Photo row centered vertically on the lower 65% of the slide. Navy background.
- **Speaker reference:** See PITCH_SCRIPT.md → [2:40–2:55]

---

## Slide 9 — Ask + Closing

- **Headline:** "Copernicus made it free. We made it actionable."
- **Body:** Help us make Europe's water the cleanest on Earth.
- **Visual:** Dark navy background, headline and body text centered. Bottom-right corner: QR code linking to the GitHub repository. Bottom-left corner: contact email (mateictaro@gmail.com). Along the very bottom strip, three logos evenly spaced: Copernicus, Galileo, EGNOS.
- **Layout:** Centered headline and subtext occupy the upper 60% of the slide. Bottom strip (15% height) holds logos and QR code. Minimalist — nothing else on the slide.
- **Speaker reference:** See PITCH_SCRIPT.md → [2:55–3:00]

---

## Pre-pitch tech checklist

- [ ] Video on slide 4 is **embedded** (file inserted), not linked from a URL. Test playback with Wi-Fi disabled.
- [ ] Autoplay-on-slide-enter enabled for the demo video on slide 4.
- [ ] Slide deck exported to PDF as a backup; a separate copy of `screencast.mp4` kept on a USB stick.
- [ ] Presenter view tested with the venue projector before the pitch.
- [ ] Slide transitions set to **instant** (no animations — they eat seconds).
