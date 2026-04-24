import numpy as np
import os
from datetime import datetime, timezone
from pathlib import Path
from sentinelhub import SentinelHubRequest, MimeType, CRS, BBox, SHConfig, DataCollection
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.elements import WKTElement


def load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if os.environ.get(key, "") == "":
            os.environ[key] = value


ROOT_DIR = Path(__file__).resolve().parents[1]
load_env_file(ROOT_DIR / "backend" / ".env")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/plasticpatrol")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "0") == "1"

# Sentinel Hub OAuth credentials
SH_CLIENT_ID = os.getenv("SH_CLIENT_ID", os.getenv("SENTINEL_HUB_CLIENT_ID", ""))
SH_CLIENT_SECRET = os.getenv("SH_CLIENT_SECRET", os.getenv("SENTINEL_HUB_CLIENT_SECRET", ""))
SH_BASE_URL = os.getenv("SH_BASE_URL", "").strip()

# Custom Evalscript for stricter debris proxy over water
EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B08"],
    output: { bands: 1, sampleType: "UINT8" }
  };
}

function evaluatePixel(sample) {
  // 1. Is it water? NDWI > 0.0 (Loosened from 0.15)
  let ndwiNumerator = sample.B03 - sample.B08;
  let ndwiDenominator = sample.B03 + sample.B08;
  let ndwi = (ndwiDenominator !== 0) ? ndwiNumerator / ndwiDenominator : 0;

  // 2. Is there an anomaly reflecting NIR? (Simple threshold)
  // Water absorbs NIR. If B08 is suspiciously high over water, flag it.
  
  if (ndwi > 0.0 && sample.B08 > 0.04) {
    return [1];
  }
  return [0];
}
"""

# Bounding box over Mediterranean Sea (coastal region)
BBOX_COORDS = [13.0, 37.0, 15.0, 39.0]
bbox = BBox(bbox=BBOX_COORDS, crs=CRS.WGS84)

# Date for query
QUERY_DATE = os.getenv("QUERY_DATE", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
GRID_WIDTH = int(os.getenv("GRID_WIDTH", "512"))
GRID_HEIGHT = int(os.getenv("GRID_HEIGHT", "512"))
MIN_COMPONENT_PIXELS = int(os.getenv("MIN_COMPONENT_PIXELS", "20"))
MAX_RELEVANT_POINTS = int(os.getenv("MAX_RELEVANT_POINTS", "2000"))


def get_mock_mask(height=512, width=512):
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[100:110, 200:210] = 1
    mask[256, 256] = 1
    mask[400:405, 450:455] = 1
    np.random.seed(42)
    random_indices = np.random.choice(height * width, 50, replace=False)
    mask.flat[random_indices] = 1
    return mask


def extract_relevant_coordinates(mask, bbox_coords, min_component_pixels, max_relevant_points):
    binary_mask = (mask == 1)
    height, width = binary_mask.shape
    visited = np.zeros_like(binary_mask, dtype=bool)
    components = []

    for row in range(height):
        for col in range(width):
            if not binary_mask[row, col] or visited[row, col]:
                continue

            stack = [(row, col)]
            visited[row, col] = True
            pixel_count = 0
            sum_row = 0
            sum_col = 0

            while stack:
                r, c = stack.pop()
                pixel_count += 1
                sum_row += r
                sum_col += c

                for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and binary_mask[nr, nc] and not visited[nr, nc]:
                        visited[nr, nc] = True
                        stack.append((nr, nc))

            if pixel_count >= min_component_pixels:
                centroid_row = int(round(sum_row / pixel_count))
                centroid_col = int(round(sum_col / pixel_count))
                components.append((pixel_count, centroid_row, centroid_col))

    components.sort(key=lambda item: item[0], reverse=True)
    components = components[:max_relevant_points]

    min_lon, min_lat, max_lon, max_lat = bbox_coords
    coordinates = []
    for _, row, col in components:
        lat_fraction = 1.0 - (row / height)
        lon_fraction = col / width
        lon = min_lon + lon_fraction * (max_lon - min_lon)
        lat = min_lat + lat_fraction * (max_lat - min_lat)
        coordinates.append((lon, lat))

    return coordinates


def fetch_and_process():
    if USE_MOCK_DATA:
        print("Using mock binary mask data")
        mask = get_mock_mask(GRID_HEIGHT, GRID_WIDTH)
    else:
        if not SH_CLIENT_ID or not SH_CLIENT_SECRET:
            raise RuntimeError("Missing Sentinel Hub credentials. Set SH_CLIENT_ID and SH_CLIENT_SECRET in backend/.env")

        sh_config = SHConfig()
        sh_config.sh_client_id = SH_CLIENT_ID
        sh_config.sh_client_secret = SH_CLIENT_SECRET

        request_collection = DataCollection.SENTINEL2_L2A
        if SH_BASE_URL:
            sh_config.sh_base_url = SH_BASE_URL
            request_collection = DataCollection.SENTINEL2_L2A.define_from(
                "SENTINEL2_L2A_CUSTOM",
                service_url=SH_BASE_URL,
            )
            if "dataspace.copernicus.eu" in SH_BASE_URL:
                sh_config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

        request = SentinelHubRequest(
            evalscript=EVALSCRIPT,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=request_collection,
                    time_interval=(f"{QUERY_DATE}T00:00:00Z", f"{QUERY_DATE}T23:59:59Z"),
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=[GRID_WIDTH, GRID_HEIGHT],
            config=sh_config,
        )

        response = request.get_data(save_data=False)
        mask = response[0].astype(np.uint8)

    coordinates = extract_relevant_coordinates(
        mask,
        BBOX_COORDS,
        min_component_pixels=MIN_COMPONENT_PIXELS,
        max_relevant_points=MAX_RELEVANT_POINTS,
    )

    db = SessionLocal()
    
    # FORCE Python to see the backend directory before importing
    import sys
    sys.path.insert(0, str(ROOT_DIR / "backend"))
    from app.db.models import PlasticDebris

    for lon, lat in coordinates:
        point = WKTElement(f"SRID=4326;POINT({lon} {lat})")
        debris = PlasticDebris(
            geom=point,
            size_category="small",
            detected_at=datetime.now(timezone.utc),
            is_collected=False,
            eco_points=5,
        )
        db.add(debris)

    db.commit()
    db.close()

    print(f"Inserted {len(coordinates)} debris points into database")


if __name__ == "__main__":
    fetch_and_process()