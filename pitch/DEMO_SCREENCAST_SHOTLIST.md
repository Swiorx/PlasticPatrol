# PlasticPatrol — 30-Second Demo Screencast Shot List

**Total runtime:** 30 seconds  
**Format:** Silent MP4, 1920×1080, 30 fps, H.264  
**Embedded in:** Pitch slide 4 — plays muted; on-screen captions carry the narrative

---

### Shot 1 (t=0–4 s)

**Action:** Browser opens to the PlasticPatrol map view showing the full Black Sea region. The camera (Leaflet `flyTo`) smoothly zooms into Constanța Port over ~2.5 seconds. As the zoom settles, red pulsing cluster dots representing Sentinel-2 detected debris fade in at approximately 44.17°N 28.65°E. Mouse cursor is visible but stationary during the zoom.

**On-screen caption:** "Sentinel-2 detects floating plastic at 10m"

**Caption styling:** Appears at bottom third of frame on a translucent dark bar (rgba 0,0,0,0.6), white text, 24 px semibold. Fade-in 0.3 s, holds for shot duration, fade-out 0.3 s.

**Backend pre-state:** Database seeded with at least one debris cluster at 44.17°N, 28.65°E in `status: "unconfirmed"`. Leaflet tile layer loaded. Cluster marker layer visible on map load.

**Expected backend response:** `GET /api/plastics` returns GeoJSON with the seeded cluster; red markers render immediately on zoom completion.

---

### Shot 2 (t=4–8 s)

**Action:** Mouse moves to one of the red debris cluster dots and clicks it. A Leaflet popup opens showing cluster metadata (location, date detected, debris confidence score) and a prominent "Reserve" button. Mouse moves to the button and clicks. A green toast notification slides up from the bottom-right corner reading "Reserved for 24h". Mouse cursor holds briefly over the toast.

**On-screen caption:** "Citizens reserve a cleanup zone"

**Caption styling:** Appears at bottom third of frame on a translucent dark bar (rgba 0,0,0,0.6), white text, 24 px semibold. Fade-in 0.3 s, holds for shot duration, fade-out 0.3 s.

**Backend pre-state:** A test user is logged in. The debris cluster is in `status: "unconfirmed"` (not yet reserved by anyone). `POST /api/plastics/{id}/reserve` endpoint is live.

**Expected backend response:** `POST /api/plastics/{id}/reserve` returns `200 OK`; cluster status updates to `"reserved"`; UI shows the toast "Reserved for 24h".

---

### Shot 3 (t=8–14 s)

**Action:** The photo-upload panel slides in from the right side of the screen (or opens as a modal). The pre-prepared beach-plastic photo file is dragged from the desktop into the drop zone — show the cursor drag motion clearly. A spinner appears for ~1 second. The spinner disappears and an ML response card animates in, displaying: `{ label: "debris", confidence: 0.94 }` with a green confidence badge. Mouse cursor rests near the card.

**On-screen caption:** "ML verifies the photo on-site"

**Caption styling:** Appears at bottom third of frame on a translucent dark bar (rgba 0,0,0,0.6), white text, 24 px semibold. Fade-in 0.3 s, holds for shot duration, fade-out 0.3 s.

**Backend pre-state:** MobileNetV2 classifier is loaded and warm. The pre-vetted test photo (a clear image of beach plastic) is on the desktop ready to drag. `POST /api/classify` is confirmed to return `{ label: "debris", confidence: 0.94 }` for this exact image — verified before recording.

**Expected backend response:** `POST /api/classify` returns `{ "label": "debris", "confidence": 0.94 }`; UI renders the response card with green badge.

---

### Shot 4 (t=14–22 s)

**Action:** Screen cuts to a full-screen black title card for exactly 1 second with centered white text: "2 days later — Sentinel-2 re-pass". Title card dissolves to the map view, which reloads around Constanța Port. The previously-red cluster dot is now absent (cluster removed or replaced by a green "confirmed-clean" marker). A blue toast notification fades in from the bottom-right: "Cleanup confirmed +6 eco-points". Mouse cursor is stationary during the map reload. Toast holds for ~3 seconds then fades out gently.

**On-screen caption:** "Satellite re-scan confirms removal"

**Caption styling:** Appears at bottom third of frame on a translucent dark bar (rgba 0,0,0,0.6), white text, 24 px semibold. Fade-in 0.3 s, holds for shot duration, fade-out 0.3 s. Caption does NOT overlap the title card — caption is suppressed during the 1-second black card.

**Backend pre-state:** Cluster is in `status: "awaiting_verification"` following the photo upload in shot 3. For demo purposes use **Option B** (see Failure Modes below): `USE_MOCK_DATA=1` is set and `POST /api/users/me/refresh-satellite` is pre-triggered to immediately mark the cluster as confirmed-clean and award eco-points. Revert `USE_MOCK_DATA` before the pitch.

**Expected backend response:** `GET /api/plastics` no longer returns the cluster (or returns it with `status: "clean"`); eco-point balance for the test user increments by 6; toast notification fires via WebSocket or polling callback.

---

### Shot 5 (t=22–30 s)

**Action:** The leaderboard view slides in from the right edge of the screen with a smooth CSS translate animation (~0.5 s). The leaderboard shows the test team currently ranked #5. Over ~2 seconds, rows animate upward: the team's row smoothly climbs past #4, #3, and settles at #2, highlighted in gold. A subtle particle burst or highlight flash marks the rank-up. After a 0.5 s hold on the leaderboard, the entire screen fades to a clean end card: dark background, PlasticPatrol logo centred, tagline below in white: "PlasticPatrol — space to shore, in one loop." End card holds for exactly 1.5 seconds. No mouse movement during end card.

**On-screen caption:** *(none — end card carries the narrative)*

**Caption styling:** No caption bar during this shot. The end card tagline IS the closing message and must be legible without a caption bar.

**Backend pre-state:** Leaderboard data seeded so the test team appears at rank #5 before the eco-points award. After the +6 points from shot 4 the team's total score must be sufficient to reach rank #2 in the seeded leaderboard. Confirm rankings in advance via `GET /api/leaderboard`.

**Expected backend response:** `GET /api/leaderboard` returns the updated rankings with the test team at #2; leaderboard UI reflects the new position after the animation sequence.

---

## Recording Specs

- **Resolution:** 1920×1080
- **Frame rate:** 30 fps
- **Codec:** H.264, MP4 container
- **Audio:** NONE — silent track only. The file must have no audio so it plays muted in the deck without surprises.
- **Software:** OBS Studio (recommended) or QuickTime Player (macOS). Browser zoom 100%. Hide bookmarks bar. Use a clean Chrome profile.
- **File output:** `screencast.mp4`, target ≤ 20 MB. Compress if needed:
  ```
  ffmpeg -i input.mp4 -vcodec h264 -crf 23 -an screencast.mp4
  ```
  (The `-an` flag strips audio entirely.)

---

## Pre-Recording Checklist

- [ ] Database seeded with at least one debris cluster near Constanța Port (`POST /api/seed` or equivalent seed script)
- [ ] Leaderboard seeded so the test team starts at rank #5 and reaches #2 after +6 eco-points
- [ ] Pre-prepared beach-plastic photo file on the desktop ready to drag-drop
- [ ] `POST /api/classify` confirmed to return `{ "label": "debris", "confidence": 0.94 }` on that exact photo (test in advance)
- [ ] `USE_MOCK_DATA=1` set and `POST /api/users/me/refresh-satellite` tested to trigger immediate cleanup confirmation
- [ ] Browser at exactly 100% zoom, fullscreen (F11), bookmarks bar hidden
- [ ] Clean test user logged in — no production data, no previous reservations
- [ ] Mouse cursor visible and reasonably sized (use OS accessibility settings if needed)
- [ ] OBS scene configured — confirm 1920×1080 canvas, no audio sources
- [ ] Do a full dry run at speed before the final take

---

## Failure Modes & Fallbacks

#### Shot 4 — 2-day satellite re-pass (trickiest section)

The 2-day satellite re-pass is not real-time. Use one of these fallbacks for the recording:

**Option A — Use a pre-confirmed cluster:**  
Seed a cluster that is already in `status: "confirmed-clean"` and demo the toast notification arriving for an existing user, simulating the moment the user receives their eco-points notification. No mock endpoint required.

**Option B — Mock the satellite-pass endpoint (recommended for recording):**  
Temporarily set `USE_MOCK_DATA=1` in your `.env` and trigger an immediate re-pass via `POST /api/users/me/refresh-satellite`. This forces the backend to mark the cluster as confirmed-clean and emit the eco-points award immediately. **Document that this is for the demo recording only and revert `USE_MOCK_DATA` to its original value before the pitch.**

### If ML returns "clean" unexpectedly

Rerun with the pre-vetted test photo — never substitute a different photo mid-recording. The shot list relies on exactly `{ "label": "debris", "confidence": 0.94 }`. If the classifier result differs, re-test the photo via `POST /api/classify` in isolation, confirm the response, then restart the take.

### If the reserve endpoint fails

Confirm the test user session token is still valid. Re-login with the clean test account, re-seed the cluster, and restart from shot 1.

---

## Editing Notes

- **One continuous take preferred.** If multiple takes are spliced together, use hard cuts only — no dissolves between shots (except the title card in shot 4 which explicitly uses a 1-second black card + dissolve to map).
- **Shot 4 title card:** "2 days later — Sentinel-2 re-pass" appears as a full-screen black title card for exactly 1 second, then dissolves (0.5 s cross-fade) to the updated map view. This is the only transition effect in the video.
- **End card in shot 5** holds for exactly 1.5 seconds — this is when the live speaker delivers the closing line over the silent video in the pitch room.
- **If total runtime exceeds 30 seconds:** trim shot 5 first (shorten the leaderboard animation to 1 second and reduce the rank-climb to just #5 → #2 in one step). Shot 4 title card can be trimmed to 0.5 s as a last resort.
- **Caption sync:** all captions should be burned into the video file (not relying on the deck's subtitle layer) so they survive export to any format. Use OBS text overlay or add via ffmpeg after recording:
  ```
  ffmpeg -i screencast_raw.mp4 -vf "drawtext=text='Your caption here':..." screencast.mp4
  ```
