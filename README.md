# 🌊 PlasticPatrol

An AI- and satellite-powered platform for **detecting, tracking, and incentivizing the cleanup of plastic debris** in oceans and on coastlines.

PlasticPatrol combines **Copernicus Sentinel-2 satellite imagery**, **ML image verification**, and a **gamified citizen engagement** system to bridge the gap between space-based remote sensing and ground-level cleanup action.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Angular 21 Frontend                  │
│          Leaflet Map · Auth · Notifications · Stats      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (REST)
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (Uvicorn)              │
│  Users · Plastics · Clusters · Classifier · Stats ·     │
│  Notifications · Satellite Scan Trigger                  │
└────────┬───────────────────────────────┬────────────────┘
         │                               │
┌────────▼────────┐          ┌───────────▼──────────────┐
│ PostGIS Database│          │  Sentinel-2 Data Pipeline │
│ (PostgreSQL 15) │          │  sentinel_fetcher.py      │
│ GeoAlchemy2     │          │  Copernicus CDSE API      │
└─────────────────┘          └──────────────────────────┘
                                         │
                              ┌──────────▼─────────────┐
                              │   ML Classifier         │
                              │   MobileNetV2 (Keras)   │
                              │   clean vs debris       │
                              └────────────────────────┘
```

---

## ✨ How It Works

### 1. Satellite Detection
A custom **evalscript** runs against Sentinel-2 L2A imagery (bands B03, B04, B06, B08, B11) applying:
- **NDWI** — confirms the pixel is water
- **FDI** (Floating Debris Index) — detects anomalous surface reflectance from plastic
- **NDVI + SWIR land-kill filters** — removes vegetation, soil, rooftops

Detected debris clusters are stored in PostGIS and displayed on the map at **10-meter resolution**.

### 2. Citizen Cleanup Flow
1. User opens the map → sees nearby debris clusters (12 km radius)
2. **Reserves** a cluster (24-hour lock)
3. Physically travels to the site and **uploads a photo** as proof
4. The **ML classifier** (MobileNetV2) verifies the photo shows real plastic
5. The next **satellite pass re-checks** the location — if water is now clean, the cleanup is confirmed and **eco-points** are awarded

### 3. Gamification
- Eco-points leaderboard
- Small / medium / large cluster tiers (2 / 4 / 6 points)
- Real-time in-app notifications for satellite confirmations

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 21, Leaflet, TypeScript |
| Backend | FastAPI, Uvicorn, APScheduler |
| Database | PostgreSQL 15 + PostGIS, GeoAlchemy2, SQLAlchemy |
| ML | TensorFlow / Keras, MobileNetV2 |
| Satellite | Sentinel Hub API, Copernicus Data Space (CDSE) |
| Auth | JWT (Bearer tokens) |
| Containerization | Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- PostgreSQL 15 with PostGIS extension
- (Optional) Sentinel Hub / CDSE credentials for live satellite data

### One-command start

```bash
./start.sh
```

This will:
1. Start PostgreSQL and create the `plasticpatrol` database with PostGIS
2. Create a Python venv and install backend dependencies
3. Start the FastAPI backend on **http://localhost:8000**
4. Install frontend npm packages and start Angular on **http://localhost:4200**

### Docker (database only)

```bash
docker-compose up -d
```

Starts a PostGIS-enabled PostgreSQL instance on port `5432`.

---

## 🔑 Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql://admin:admin123@localhost:5432/plasticpatrol

# Sentinel Hub credentials (optional — mock data used if missing)
SH_CLIENT_ID=your_client_id
SH_CLIENT_SECRET=your_client_secret
SH_BASE_URL=https://sh.dataspace.copernicus.eu

# Optional tuning
USE_MOCK_DATA=0
USE_PRESET_LOCATIONS=true
PRESET_LOCATION_SET=world_hotspots
TARGET_RESOLUTION_METERS=10
MIN_COMPONENT_PIXELS=12
MAX_RELEVANT_POINTS=1200
```

---

## 📡 API Overview

Interactive docs available at **http://localhost:8000/docs** once the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/users/register` | Register a new user |
| `POST` | `/api/users/login` | Login, receive JWT token |
| `GET` | `/api/users/me` | Get current user profile |
| `POST` | `/api/users/me/location` | Update user's GPS location |
| `GET` | `/api/users/me/debris` | Debris clusters near user |
| `POST` | `/api/users/me/refresh-satellite` | Trigger satellite scan for user area |
| `GET` | `/api/plastics/` | All debris (paginated, filterable) |
| `POST` | `/api/plastics/report` | Manually report beach debris |
| `POST` | `/api/plastics/scan/start` | Trigger global satellite scan |
| `GET` | `/api/plastics/export/geojson` | Export all debris as GeoJSON |
| `POST` | `/api/clusters/reserve` | Reserve a debris cluster |
| `POST` | `/api/clusters/{id}/collect` | Submit photo proof + ML verify |
| `POST` | `/api/classify` | Classify an image (debris / clean) |
| `GET` | `/api/stats/` | Platform-wide statistics |
| `GET` | `/api/notifications/` | User notifications |

---

## 🤖 ML Classifier

The classifier (`ml_classifier/`) is a **MobileNetV2-based binary model** trained on ocean imagery:

- **Input**: 224×224 RGB image
- **Output**: `{ "label": "debris" | "clean", "confidence": float }`
- **Training data**: `data/clean/` and `data/debris/` directories

To retrain:

```bash
python -m ml_classifier.train --data_dir ./data --epochs 20
```

---

## 🛰️ Satellite Pipeline

Run a manual scan against preset hotspot regions:

```bash
python data_pipeline/sentinel_fetcher.py
```

Tuning guide:

```bash
python data_pipeline/sentinel_fetcher.py --tuning-help
```

**Preset regions**: Constanța Port, Bosphorus, Rotterdam, Singapore Strait, LA/Long Beach, Rio de Janeiro, Malta Channel.

---

## 🌱 Seeding Test Data

```bash
# Via Swagger UI → POST /api/seed
# Or with curl:
curl -X POST http://localhost:8000/api/seed
```

Creates 2 users (`admin` / `testuser`, password: `admin123`) and 7 sample debris points.

---

## 👥 Team

| Name | Role |
|---|---|
| **Rares Neacsu** | 🛰️ Backend & Satellite Pipeline Lead |
| **Matei Necula** | 🤖 Full-Stack & ML Developer |
| **Andrei Stan** | 🗺️ Frontend & Map Developer |
| **Swiorx** | 🔌 Backend & API Developer |

---

## 📄 License

MIT
