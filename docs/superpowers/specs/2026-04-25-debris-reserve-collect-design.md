# Debris Reserve & Collect Flow — Design Spec
Date: 2026-04-25

## Overview

Users see debris clusters on the map, reserve a cluster for 24 hours (hiding it from others), physically approach within 100m, photograph it, and have the photo ML-verified. On ML pass the cluster is marked collected and disappears for everyone until satellite re-verification. Eco points are awarded only after sentinel confirms the debris is gone.

---

## Data Model

### New table: `cluster_reservations`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `point_ids` | JSON | Array of `PlasticDebris.id`s resolved at reservation time |
| `cluster_center_lat` | Float | Snapshot of cluster center for server-side proximity check |
| `cluster_center_lon` | Float | |
| `eco_points` | Integer | Snapshot from cluster at reservation time |
| `reserved_by` | FK → users.id | |
| `reserved_until` | DateTime (UTC) | `created_at + 24h` |
| `attempt_count` | Integer | Default 0, max 3 |
| `status` | String | `reserved` → `photo_verified` → `collected`; or `expired` / `failed` |
| `created_at` | DateTime (UTC) | |

### Changes to `PlasticDebris`
- Add `is_reserved` Boolean, default False — set True when a cluster containing this point is reserved; cleared on expiry/failure/collection confirmed.

No changes to `User` or `Notification`.

---

## Backend API

### New router: `/api/clusters`

#### `POST /api/clusters/reserve`
- Auth: JWT required
- Body: `{ point_ids: int[], center_lat: float, center_lon: float, eco_points: int }`
- Logic:
  1. Check current user has no active reservation (`status IN ('reserved','photo_verified')`) — if they do, return 409 "You already have an active reservation"
  2. Check none of `point_ids` have `is_reserved=True` — if any do, return 409 "Already reserved by another user"
  3. Create `ClusterReservation` with `status=reserved`, `reserved_until=now+24h`
  4. Set `is_reserved=True` on all `PlasticDebris` rows in `point_ids`
  5. Return reservation id and `reserved_until`

#### `POST /api/clusters/{reservation_id}/collect`
- Auth: JWT required, must be `reserved_by` owner
- Body: multipart form — `file` (image/jpeg, image/png, image/webp, max 10MB)
- Server-side proximity check: haversine(user lat/lon from JWT session vs `cluster_center_lat/lon`) must be ≤ 100m — else 400 "Too far from debris"
- Logic:
  1. Verify reservation exists, status=`reserved`, not expired, owned by current user
  2. Increment `attempt_count`
  3. Run ML classifier on uploaded image
  4. **ML pass (debris detected):**
     - Set reservation `status=photo_verified`
     - Set `is_collected=True`, `collected_by=user.id`, `collected_at=now` on all point rows
     - `is_reserved` stays True (cluster hidden from map for everyone until sentinel pass)
     - Return 200 "Collected — awaiting satellite confirmation for eco points"
  5. **ML fail (no debris detected):**
     - If `attempt_count < 3`: return 422 with attempts remaining
     - If `attempt_count >= 3`: set status=`failed`, clear `is_reserved` on all point rows, send Notification to user "Reservation released after 3 failed attempts", return 422
  6. **ML error (500):** treat as fail — increment `attempt_count`, same branching as ML fail

#### `DELETE /api/clusters/{reservation_id}/reserve`
- Auth: JWT required, must be owner
- Releases reservation: status=`expired`, clear `is_reserved` on point rows
- Returns 204

### Changes to existing endpoints

`GET /api/plastic/` and `GET /api/users/me/debris`:
- Exclude rows where `is_reserved=True` AND `reserved_by != current_user.id`
- The reserving user still sees their own reserved cluster

### Background job (APScheduler, runs every 5 minutes)

Query `ClusterReservation` where `status='reserved'` AND `reserved_until < now()`:
- For each expired reservation:
  1. Set `status=expired`
  2. Clear `is_reserved=False` on all point rows in `point_ids`
  3. Send `Notification` to `reserved_by`: "Your reservation expired — debris is available again"

### Sentinel re-verification integration

After sentinel scan inserts/updates points, for each `PlasticDebris` where `is_collected=True` AND `is_verified=False`:
- **Debris no longer detected by sentinel (confirmed gone):**
  1. Set `is_verified=True`
  2. Find `ClusterReservation` by matching `point_ids` containing this debris id
  3. Set reservation `status=collected`
  4. Award `eco_points` (from reservation snapshot) to `reserved_by` user
  5. Send Notification: "Satellite confirmed collection! You earned X eco points"
- **Debris still detected by sentinel (collection failed):**
  1. Revert `is_collected=False`, clear `is_reserved=False`
  2. Set reservation `status=failed`
  3. Send Notification: "Satellite couldn't confirm collection — debris reappears on map"
  4. No eco points awarded (they were never granted)

Note: sentinel skips points where `is_reserved=True` and `is_collected=False` (actively reserved, not yet photo-verified) to avoid false negatives during the reservation window.

---

## Frontend

### Map component (`map.ts`)

- Cluster marker click → popup showing: size category, eco_points, point count, "Reserve" button
- On reserve: call `POST /api/clusters/reserve`, store `reservation_id` and `cluster_center_lat/lon` in component state
- Reserved cluster (own): distinct icon, show "Collect" button in popup
  - "Collect" button enabled only when `haversineMeters(userLat, userLon, centerLat, centerLon) <= 100`
  - Re-evaluated on every GPS position update
  - If user drifts beyond 100m, button disables with tooltip "Get closer to collect"
- Other users' reserved clusters: filtered server-side, never rendered

### New component: `CollectOverlay`

Full-screen overlay triggered by "Collect" button:

**States:**
1. **Idle**: file/camera input + "Submit Photo" button
2. **Loading**: spinner, input disabled
3. **ML fail (retries left)**: "No debris detected. X tries remaining." — stays open
4. **ML fail (no retries)**: "Reservation released after 3 failed attempts." — closes overlay, removes cluster marker
5. **ML pass**: "Collected! Waiting for satellite confirmation to award eco points." — closes overlay, removes cluster marker
6. **Network/server error**: "Verification failed. Please retry." — stays open, counts as attempt

### Notification display

Surfaces the following messages (existing notification bell):
- Reservation expired (24h timeout)
- Satellite confirmed collection + eco points awarded
- Satellite denied collection + debris reappears

---

## Error Cases & Edge Cases

| Scenario | Handling |
|---|---|
| Two users reserve same cluster simultaneously | DB transaction: first write wins, second gets 409 |
| User moves away mid-collection overlay | Submit re-checks proximity server-side — returns 400 if > 100m |
| Sentinel re-scans before reservation expires | Sentinel skips `is_reserved=True AND is_collected=False` points |
| User with reservation gets deleted | Cascade: reservation `expired`, `is_reserved` cleared on point rows |
| ML classifier returns 500 | Counted as failed attempt, user sees "Verification failed, please retry" |
| Cluster points span >100m radius | Proximity uses cluster centroid — user needs to be within 100m of centroid |

---

## Out of Scope

- Admin dashboard for reservation monitoring
- Partial cluster collection (all-or-nothing per cluster)
- Multiple concurrent reservations per user — one active reservation at a time is enforced
