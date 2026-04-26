## Rehearsal notes

- **Slide 1 (Hook):** Speak slowly — pause after "11 million tonnes." Let the number land before you move on.
- **Slides 3 & 5 (Tech):** Slightly faster, punchy. One beat between each stage / bullet.
- **Slide 4 (Demo):** Start the screencast playing as you say the first sentence. Narrate confidently — you are the audio track.
- **Slide 9 (Ask):** Slow right down. Make eye contact with the panel on "Copernicus made the data free."
- **If running long:** Cut the second sentence of slide 7 first, then drop slide 5's third bullet.

---

### [0:00–0:20] Slide 1 — Hook

Every year, eleven million tonnes of plastic enter our oceans. Eleven million. Sentinel-2 satellites orbit overhead and they can see it — floating debris patches mapped to ten metres. But until now, nobody connected those satellites to the people on the ground who could actually clean it up. We built that connection.

---

### [0:20–0:40] Slide 2 — The Problem

Detection alone is not cleanup. The EU's new EPR and PPWR regulations force plastic producers to fund verified removal — not just awareness campaigns, audited proof. Today there is no tool that closes the full loop from space detection down to ground action and back to a satellite audit. That gap is our wedge.

---

### [0:40–1:00] Slide 3 — The Solution

PlasticPatrol runs in three stages. First, Sentinel-2 satellites detect debris clusters using our custom evalscript. Second, citizens on our app reserve a cluster, clean it, and upload a photo — our MobileNetV2 classifier verifies it on the spot. Third, two days later a satellite re-pass confirms the debris is gone. Detection, action, confirmation — fully automated.

---

### [1:00–1:35] Slide 4 — Demo

Here you see our live map zoomed into Constanța, Romania. Red clusters are plastic hotspots flagged by the satellite pipeline — fresh from this morning's pass. A citizen taps one, reserves it, and it turns orange — locked for 48 hours. They go clean it up, upload their photo right here in the app. Watch the classifier: green tick, verified in two seconds. Two days later the satellite re-pass fires — the algorithm sees clean water, the cluster disappears from the map, and eco-points land in the citizen's account. Space to street to space, fully automated.

---

### [0:95–1:55] Slide 5 — Why It's Innovative

Three things make this novel. One: our Sentinel-2 evalscript combines NDWI, FDI, NDVI, and SWIR at full ten-metre resolution — purpose-built for floating plastic. Two: the closed-loop satellite-to-citizen-to-satellite verification — no other platform does this. Three: every cleanup generates labelled ground-truth data, improving the model for free.

---

### [1:55–2:25] Slide 6 — Business Model

We run a hybrid flywheel. Citizens use the app free and generate verified cleanups at zero marginal cost to us. Corporates — Coca-Cola, Nestlé — buy those cleanup credits to meet EU PPWR obligations. Think carbon credits but for plastic, priced per kilogram of confirmed removal. Ports and agencies like EMSA pay for SaaS dashboards: real-time maps, compliance reports, trend analytics. Citizens feed the flywheel; corporates and governments pay to access it.

---

### [2:25–2:40] Slide 7 — Market & Traction

The EU plastic EPR market hits one-and-a-half billion euros by 2027. Our pipeline is already running — Black Sea hotspots detected, Constanța Port identified as a pilot-ready partner. We are not pitching a concept; we are pitching a working system.

---

### [2:40–2:55] Slide 8 — Team

Four engineers: Rares Neacsu on backend and the satellite pipeline, Matei Necula on full-stack and machine learning, Andrei Stan on frontend and maps, and Swiorx on backend and API integration. We built the full stack in 48 hours — that is the team you fund.

---

### [2:55–3:00] Slide 9 — Ask

Copernicus made the data free. We made it actionable. Help us make Europe's water the cleanest on Earth.
