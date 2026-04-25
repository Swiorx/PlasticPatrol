# Auth, Per-User Location & Scoped Sentinel Fetch — Design

Date: 2026-04-25
Status: Draft (awaiting user review)

## Goal

1. Add a real login/register UI in the Angular frontend, wired to the existing FastAPI JWT endpoints.
2. Protect the `/map` route — only authenticated users can access it.
3. Persist each user's current location (lat/lon) in the database via an authenticated POST.
4. Serve plastic-debris data scoped to the user's surrounding area (12 km radius) via an authenticated GET.
5. Allow on-demand Sentinel scanning of the user's area, refactoring the existing CLI script into a callable function.

## Out of scope

- Password reset / email verification.
- Refresh tokens (single short-lived JWT is enough for now).
- Location history (only the *current* location is kept).
- A periodic/scheduled Sentinel job (manual refresh only, for now).
- Production-grade UI styling — barebones HTML/CSS only, owner will redesign.

---

## Architecture overview

```
[Angular]                                    [FastAPI]                       [Postgres/PostGIS]
 Login/Register pages
        │ POST /api/users/login (form)
        │ POST /api/users/register (json)
        ▼
 AuthService (token in localStorage)
        │
        │ HttpInterceptor attaches "Authorization: Bearer <jwt>"
        ▼
 authGuard ──► /map (protected)
        │
 Map component
        │ POST /api/users/me/location {lat, lon}     ──►  UPDATE users SET latitude, longitude, last_location_at
        │ GET  /api/users/me/debris?radius_km=12     ──►  SELECT debris WHERE ST_DWithin(geom, user_point, 12000)
        │ POST /api/users/me/refresh-satellite       ──►  fetch_for_bbox(user_bbox) → insert new debris (dedup) → return count
```

Two distinct concerns are separated:

- **Read path** (`GET /me/debris`) — fast, hits DB only, scoped via PostGIS `ST_DWithin`.
- **Write/scan path** (`POST /me/refresh-satellite`) — slow, calls Sentinel Hub, inserts into shared `plastic_debris` table.

---

## Backend changes

### 1. `User` model — add location columns

In `backend/app/db/models.py`:

```python
latitude  = Column(Float, nullable=True)
longitude = Column(Float, nullable=True)
last_location_at = Column(DateTime, nullable=True)
```

No migration framework is in use — schema is created via `Base.metadata.create_all`. New columns will appear on fresh DBs. For existing dev DBs, document a manual `ALTER TABLE` (or `docker-compose down -v`).

### 2. Schemas — `backend/app/schemas/user.py`

Add:

```python
class LocationIn(BaseModel):
    latitude: float   # -90..90
    longitude: float  # -180..180

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
```

Add field validators on `latitude`/`longitude` ranges. Tighten `UserCreate.password` to `min_length=8`.

### 3. Routes — `backend/app/api/routes/users.py`

- **Improve `register`**: enforce password ≥ 8 chars (via schema), return `TokenOut` (auto-login after register), match login response shape.
- **Add `POST /me/location`** (protected): accepts `LocationIn`, updates the current user's `latitude`, `longitude`, `last_location_at`. Returns `UserOut`.
- **Add `GET /me/debris`** (protected): reads current user's coords; if missing → `400 "Location not set"`. Computes a 12 km radius (configurable via `?radius_km=` query, default 12, clamp 1..50). Returns list of `{id, latitude, longitude, size_category, is_collected, eco_points}` filtered by `ST_DWithin(cast(geom, Geography), cast(user_point, Geography), radius_meters)`.
- **Add `POST /me/refresh-satellite`** (protected): builds a bbox of ~12 km around the user (using the same `meters_per_degree_lon` math from the fetcher), calls `data_pipeline.sentinel_fetcher.fetch_for_bbox(bbox)`, inserts new debris with the same dedup logic that exists today, returns `{inserted: N}`.

### 4. Refactor `data_pipeline/sentinel_fetcher.py`

Currently the module reads env vars at import time (BBOX, GRID size) and `fetch_and_process()` does both fetching and DB writes. Split it:

- Move env-driven globals into `_load_cli_config()` (only run when `__main__`).
- Extract pure function:
  ```python
  def fetch_for_bbox(bbox: list[float],
                    *,
                    use_mock: bool | None = None,
                    target_resolution_m: float = 10.0,
                    max_dimension: int = 2500,
                    start_date: str | None = None,
                    end_date: str | None = None) -> list[tuple[float, float]]:
      """Run the Sentinel evalscript on `bbox` and return [(lat, lon), ...] centroids."""
  ```
- The existing CLI flow keeps working by calling `fetch_for_bbox` then doing the DB writes it does today.
- The new `/me/refresh-satellite` endpoint calls `fetch_for_bbox` and reuses the same dedup-insert block (extract that into `_insert_new_debris(db, coords)` helper to avoid duplication).

### 5. `bbox_for_user(lat, lon, radius_km=12)` helper

Place in `backend/app/services/geo.py` (new file). Uses `meters_per_degree_lon` already in the fetcher (move/share it). Returns `[min_lon, min_lat, max_lon, max_lat]`.

---

## Frontend changes

Stack: Angular standalone components, barebones styling (plain CSS, no design system).

### 1. New service — `frontend/src/app/services/auth.service.ts`

- `login(usernameOrEmail, password)` → POST form-encoded to `/api/users/login`, stores `access_token` in `localStorage` under key `pp_token`, fetches `/api/users/me`, exposes `currentUser$` signal/BehaviorSubject.
- `register(username, email, password)` → POST JSON to `/api/users/register`, expects `TokenOut`, stores token, sets currentUser.
- `logout()` → clears token + user.
- `isLoggedIn()` → boolean from token presence (no expiry check client-side; server rejects expired tokens).
- `token()` → string | null.

### 2. New service — `frontend/src/app/services/api.service.ts` (thin)

Methods: `postLocation({lat, lon})`, `getDebris(radiusKm = 12)`, `refreshSatellite()`. Uses `HttpClient`.

### 3. HTTP interceptor — `frontend/src/app/core/auth.interceptor.ts`

Functional interceptor; attaches `Authorization: Bearer <token>` if token present. Registered via `provideHttpClient(withInterceptors([authInterceptor]))` in `app.config.ts`.

### 4. Guard — `frontend/src/app/core/auth.guard.ts`

Functional `CanActivateFn` that checks `AuthService.isLoggedIn()`; otherwise redirects to `/login` with `returnUrl` query param.

### 5. New components

- `LoginComponent` (`/login`): form with username/email + password. On success, redirect to `returnUrl` or `/map`. Link to `/register`.
- `RegisterComponent` (`/register`): form with username, email, password, confirm-password. Client-side validation: passwords match, password ≥ 8 chars, valid email. On success → auto-login → `/map`.
- Both: barebones styling, errors displayed inline from server response.

### 6. Routes — `frontend/src/app/app.routes.ts`

```ts
{ path: '', component: Home },
{ path: 'login', component: LoginComponent },
{ path: 'register', component: RegisterComponent },
{ path: 'map', component: Map, canActivate: [authGuard] },
{ path: '**', redirectTo: '' }
```

### 7. `Map` component changes (`frontend/src/app/components/map/map.ts`)

- Inject `ApiService`.
- On geolocation success: also `apiService.postLocation({lat, lon})` (debounced — at most 1 request / 30s; only if moved > ~50 m to avoid spam).
- After first location obtained, call `getDebris(12)` and render returned points as Leaflet markers (different icon than user marker).
- Add a "Refresh satellite scan" button → calls `refreshSatellite()` → on success re-fetches `getDebris`.
- Handle 401 → redirect to `/login` (interceptor or local handling).

### 8. Header (`header.html`)

- Show "Login" / "Register" when logged out.
- Show "Logout" + username when logged in.
- Hook into `AuthService.currentUser$`.

---

## Data flow examples

### Logging in and viewing the map

1. User submits `/login` form → `POST /api/users/login` → token stored.
2. Navigate to `/map` (guard passes).
3. Browser geolocation fires → `POST /me/location` → server stores lat/lon.
4. `GET /me/debris?radius_km=12` → returns DB-filtered points → markers rendered.
5. (Optional) User clicks "Refresh satellite scan" → `POST /me/refresh-satellite` → server scans 12 km bbox → inserts new debris → frontend re-fetches `/me/debris`.

### Unauthenticated access to `/map`

1. User navigates to `/map`.
2. `authGuard` sees no token → redirect `/login?returnUrl=/map`.
3. After login, redirected back.

---

## Error handling

- **No location set yet** when `/me/debris` is called → `400 {detail: "Location not set"}`. Frontend shows "Share your location to load nearby debris".
- **Geolocation denied** in browser → existing `errorMsg` UI; debris fetch is skipped.
- **Sentinel fetch failure** (missing creds, network) → `500 {detail: "..."}`; frontend shows toast/inline error, map keeps previous markers.
- **401 from API** → interceptor or component clears token and redirects to `/login`.

## Testing

- Backend: pytest for `/me/location`, `/me/debris` (with/without auth, with/without location, radius clamp), and `bbox_for_user`. Mock `fetch_for_bbox` for the refresh endpoint test.
- Frontend: smoke-test `AuthService` (token persistence) + guard redirect. UI tests skipped per "barebones" scope.

## Configuration / env

No new env vars required. Existing Sentinel Hub creds in `backend/.env` are reused by `fetch_for_bbox`.

## Migration note

For existing dev databases, run once:

```sql
ALTER TABLE users
  ADD COLUMN latitude DOUBLE PRECISION,
  ADD COLUMN longitude DOUBLE PRECISION,
  ADD COLUMN last_location_at TIMESTAMP;
```

Or wipe the dev DB (`docker-compose down -v`).
