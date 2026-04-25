import numpy as np
import os
import argparse
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sentinelhub import SentinelHubRequest, MimeType, CRS, BBox, SHConfig, DataCollection, MosaickingOrder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
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
TARGET_RESOLUTION_METERS = float(os.getenv("TARGET_RESOLUTION_METERS", "10"))
MAX_GRID_DIMENSION = int(os.getenv("MAX_GRID_DIMENSION", "2500"))

# Predefined locations sized so 10m pixel resolution remains practical.
PRESET_LOCATION_SETS = {
    "world_hotspots": [
        {"name": "constanta_port", "bbox": [28.55, 44.05, 28.75, 44.22]},
        {"name": "bosphorus", "bbox": [28.90, 40.90, 29.15, 41.10]},
        {"name": "rotterdam_port", "bbox": [3.90, 51.90, 4.22, 52.10]},
        {"name": "singapore_strait", "bbox": [103.70, 1.15, 103.92, 1.35]},
        {"name": "la_long_beach", "bbox": [-118.35, 33.65, -118.11, 33.85]},
        {"name": "rio_port", "bbox": [-43.33, -23.08, -43.10, -22.90]},
        {"name": "malta_channel", "bbox": [14.20, 35.85, 14.45, 36.05]},
    ],
    "constanta_only": [
        {"name": "constanta_port", "bbox": [28.55, 44.05, 28.75, 44.22]},
    ],
}


def parse_bbox_env(raw_bbox):
    """Parse SENTINEL_BBOX from env as 'min_lon,min_lat,max_lon,max_lat'."""
    if not raw_bbox:
        return None

    normalized = raw_bbox.strip().lower()
    if normalized in {"world", "global", "all"}:
        return [-180.0, -90.0, 180.0, 90.0]

    parts = [part.strip() for part in raw_bbox.split(",")]
    if len(parts) != 4:
        raise ValueError("SENTINEL_BBOX must have 4 comma-separated numbers: min_lon,min_lat,max_lon,max_lat")

    try:
        min_lon, min_lat, max_lon, max_lat = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError("SENTINEL_BBOX must contain valid numeric values") from exc

    if not (-180.0 <= min_lon < max_lon <= 180.0):
        raise ValueError("SENTINEL_BBOX longitude bounds must satisfy -180 <= min_lon < max_lon <= 180")
    if not (-90.0 <= min_lat < max_lat <= 90.0):
        raise ValueError("SENTINEL_BBOX latitude bounds must satisfy -90 <= min_lat < max_lat <= 90")

    return [min_lon, min_lat, max_lon, max_lat]


def parse_bool_env(var_name, default):
    raw = os.getenv(var_name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def is_world_bbox(bbox_coords):
    min_lon, min_lat, max_lon, max_lat = bbox_coords
    return (
        abs(min_lon + 180.0) < 1e-9 and
        abs(min_lat + 90.0) < 1e-9 and
        abs(max_lon - 180.0) < 1e-9 and
        abs(max_lat - 90.0) < 1e-9
    )


def parse_positive_int(raw_value, var_name):
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{var_name} must be an integer") from exc

    if value <= 0:
        raise ValueError(f"{var_name} must be > 0")

    return value


def clamp(value, low, high):
    return max(low, min(value, high))


def estimate_grid_from_bbox(bbox_coords, target_pixels):
    min_lon, min_lat, max_lon, max_lat = bbox_coords
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat

    # Preserve bbox aspect ratio while keeping total pixels under a practical cap.
    aspect_ratio = max(0.25, min(8.0, lon_span / max(lat_span, 1e-6)))
    width = int(round(math.sqrt(target_pixels * aspect_ratio)))
    height = int(round(width / aspect_ratio))
    width = clamp(width, 256, 2048)
    height = clamp(height, 256, 2048)
    return width, height


def meters_per_degree_lon(lat_deg):
    return 111320.0 * max(0.1, math.cos(math.radians(lat_deg)))


def grid_for_10m_resolution(bbox_coords, target_resolution_meters=10.0, max_dimension=2500):
    min_lon, min_lat, max_lon, max_lat = bbox_coords
    center_lat = (min_lat + max_lat) / 2.0

    width_m = (max_lon - min_lon) * meters_per_degree_lon(center_lat)
    height_m = (max_lat - min_lat) * 111320.0

    width_px = int(math.ceil(width_m / target_resolution_meters))
    height_px = int(math.ceil(height_m / target_resolution_meters))
    width_px = max(1, width_px)
    height_px = max(1, height_px)

    if width_px > max_dimension or height_px > max_dimension:
        raise ValueError(
            f"BBox {bbox_coords} needs {width_px}x{height_px} pixels at {target_resolution_meters}m/px, "
            f"which exceeds MAX_GRID_DIMENSION={max_dimension}. Use smaller preset areas or increase MAX_GRID_DIMENSION."
        )

    return width_px, height_px


def resolve_region_requests():
    use_presets = parse_bool_env("USE_PRESET_LOCATIONS", True)
    preset_name = os.getenv("PRESET_LOCATION_SET", "world_hotspots").strip() or "world_hotspots"

    if use_presets:
        if preset_name not in PRESET_LOCATION_SETS:
            available = ", ".join(sorted(PRESET_LOCATION_SETS.keys()))
            raise ValueError(f"Unknown PRESET_LOCATION_SET '{preset_name}'. Available: {available}")
        selected_regions = PRESET_LOCATION_SETS[preset_name]
    else:
        selected_regions = [{"name": "custom_bbox", "bbox": BBOX_COORDS}]

    region_requests = []
    for region in selected_regions:
        region_bbox = region["bbox"]
        width, height = grid_for_10m_resolution(
            region_bbox,
            target_resolution_meters=TARGET_RESOLUTION_METERS,
            max_dimension=MAX_GRID_DIMENSION,
        )
        region_requests.append(
            {
                "name": region["name"],
                "bbox": region_bbox,
                "width": width,
                "height": height,
            }
        )

    return region_requests


def resolve_grid_dimensions(bbox_coords):
    raw_width = os.getenv("GRID_WIDTH", "").strip()
    raw_height = os.getenv("GRID_HEIGHT", "").strip()
    world_bbox = is_world_bbox(bbox_coords)

    default_target_pixels = "524288" if world_bbox else "786432"
    target_pixels = parse_positive_int(os.getenv("TARGET_GRID_PIXELS", default_target_pixels), "TARGET_GRID_PIXELS")

    if raw_width and raw_height:
        return parse_positive_int(raw_width, "GRID_WIDTH"), parse_positive_int(raw_height, "GRID_HEIGHT")

    estimated_width, estimated_height = estimate_grid_from_bbox(bbox_coords, target_pixels)

    if raw_width:
        width = parse_positive_int(raw_width, "GRID_WIDTH")
        aspect = estimated_width / max(estimated_height, 1)
        height = clamp(int(round(width / max(aspect, 1e-6))), 256, 4096)
        return width, height

    if raw_height:
        height = parse_positive_int(raw_height, "GRID_HEIGHT")
        aspect = estimated_width / max(estimated_height, 1)
        width = clamp(int(round(height * aspect)), 256, 4096)
        return width, height

    return estimated_width, estimated_height


def print_tuning_help():
    region_requests = resolve_region_requests()

    print("Sentinel Fetcher tuning guide")
    print("--------------------------------")
    print(f"Target map quality: 1 pixel ~= {TARGET_RESOLUTION_METERS:.1f} meters")
    print(f"Using preset locations: {parse_bool_env('USE_PRESET_LOCATIONS', True)}")
    print(f"Active preset: {os.getenv('PRESET_LOCATION_SET', 'world_hotspots')}")
    print("\nActive regions:")
    for region in region_requests:
        min_lon, min_lat, max_lon, max_lat = region["bbox"]
        center_lat = (min_lat + max_lat) / 2.0
        lon_m_per_px = ((max_lon - min_lon) * meters_per_degree_lon(center_lat)) / region["width"]
        lat_m_per_px = ((max_lat - min_lat) * 111320.0) / region["height"]
        print(
            f"- {region['name']}: bbox={region['bbox']} grid={region['width']}x{region['height']} "
            f"(~{lon_m_per_px:.1f}m/px lon, ~{lat_m_per_px:.1f}m/px lat)"
        )

    print("\nVariables you can tweak:")
    print("- USE_PRESET_LOCATIONS: true/false, default true")
    print("- PRESET_LOCATION_SET: world_hotspots or constanta_only")
    print("- TARGET_RESOLUTION_METERS: default 10 (map quality)")
    print("- MAX_GRID_DIMENSION: safety cap for each region grid")
    print("- SENTINEL_BBOX: used only if USE_PRESET_LOCATIONS=false")
    print("- MIN_COMPONENT_PIXELS: higher values reduce small noisy detections")
    print("- MAX_RELEVANT_POINTS: global cap for inserted detections")

    print("\nRecommended low-noise setup:")
    print("- export USE_PRESET_LOCATIONS=true")
    print("- export PRESET_LOCATION_SET=world_hotspots")
    print("- export TARGET_RESOLUTION_METERS=10")
    print("- export MIN_COMPONENT_PIXELS=12")
    print("- export MAX_RELEVANT_POINTS=1200")
    print("\nFor more sensitivity: reduce MIN_COMPONENT_PIXELS. For less noise: increase it.")

EVALSCRIPT = """
//VERSION=3

function setup() {
    return {
        input: ["B03", "B04", "B06", "B08", "B11"],
        output: { bands: 1, sampleType: "UINT8" }
    };
}

function evaluatePixel(sample) {

    // ── STAGE 1: ABSOLUTE LAND KILL
    // Rooftops, roads, soil all have high SWIR — water never does
    if (sample.B11 > 0.07) return [0];
    // Vegetation: high NIR spike
    if (sample.B08 > 0.15) return [0];
    // Urban/bare soil: red channel high relative to blue/green
    if (sample.B04 > 0.15) return [0];

    // ── STAGE 2: NDWI — must be clearly water
    let ndwiDen = sample.B03 + sample.B08;
    let ndwi = (ndwiDen !== 0) ? (sample.B03 - sample.B08) / ndwiDen : 0;
    if (ndwi < 0.10) return [0];  // anything below this is not water

    // ── STAGE 3: BAND RATIO WATER CONFIRMATION
    // Water: green dominates, red is low, NIR is very low
    // Land/roof: all bands relatively higher and more balanced
    let greenRedRatio = sample.B03 / (sample.B04 + 0.001);
    if (greenRedRatio < 1.0) return [0]; // red >= green = not water

    let nirGreenRatio = sample.B08 / (sample.B03 + 0.001);
    if (nirGreenRatio > 0.80) return [0]; // NIR too high relative to green = land

    // ── STAGE 4: FDI
    let factor = (842 - 665) / (1610 - 665);
    let fdi = sample.B08 - (sample.B06 + (sample.B11 - sample.B06) * factor * 10);

    // ── STAGE 5: NDVI
    let ndviDen = sample.B08 + sample.B04;
    let ndvi = (ndviDen !== 0) ? (sample.B08 - sample.B04) / ndviDen : 0;
    if (ndvi > 0.08) return [0]; // any vegetation signal = reject

    // ── STAGE 6: WATER TYPE + DEBRIS THRESHOLD
    let isOcean   = (ndwi > 0.25 && sample.B08 < 0.05 && sample.B11 < 0.04);
    let isCoastal = (ndwi > 0.10 && ndwi <= 0.25 && sample.B08 < 0.10);

    if (isOcean   && fdi > 0.05) return [1];
    if (isCoastal && fdi > 0.03) return [1];

    return [0];
}
"""

# Bounding box (defaults to whole world). Override with SENTINEL_BBOX.
DEFAULT_BBOX_COORDS = [-180.0, -90.0, 180.0, 90.0] #A SE SCHIMBA IN FUNCTIE DE LOCATIA USERULUI
BBOX_COORDS = parse_bbox_env(os.getenv("SENTINEL_BBOX", "")) or DEFAULT_BBOX_COORDS
bbox = BBox(bbox=BBOX_COORDS, crs=CRS.WGS84)

# Time window for query (default: last 30 days, to increase chance of available scenes)
QUERY_END_DATE = os.getenv("QUERY_END_DATE", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
QUERY_START_DATE = os.getenv(
    "QUERY_START_DATE",
    (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
)
GRID_WIDTH, GRID_HEIGHT = resolve_grid_dimensions(BBOX_COORDS)
MIN_COMPONENT_PIXELS = int(os.getenv("MIN_COMPONENT_PIXELS", "6" if is_world_bbox(BBOX_COORDS) else "3"))
MAX_RELEVANT_POINTS = int(os.getenv("MAX_RELEVANT_POINTS", "3000" if is_world_bbox(BBOX_COORDS) else "2000"))


def get_mock_mask(height=512, width=512):
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[100:110, 200:210] = 1
    # Only set center pixel if dimensions are large enough
    if height > 256 and width > 256:
        mask[256, 256] = 1
    else:
        # For smaller masks, set the approximate center
        center_row = min(height - 1, height // 2)
        center_col = min(width - 1, width // 2)
        mask[center_row, center_col] = 1
    # Only add third region if dimensions are large enough
    if height > 405 and width > 455:
        mask[400:405, 450:455] = 1
    np.random.seed(42)
    random_indices = np.random.choice(height * width, min(50, height * width), replace=False)
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
        # Return tuples as (lat, lon) as requested.
        coordinates.append((lat, lon))

    return coordinates


def fetch_and_process():
    region_requests = resolve_region_requests()

    if USE_MOCK_DATA:
        print("Using mock binary mask data")
        region_results = []
        for region in region_requests:
            mask = get_mock_mask(region["height"], region["width"])
            region_results.append(
                {
                    "name": region["name"],
                    "bbox": region["bbox"],
                    "mask": mask,
                    "width": region["width"],
                    "height": region["height"],
                }
            )
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

        def build_request(evalscript, region_bbox, width, height):
            return SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=request_collection,
                        time_interval=(f"{QUERY_START_DATE}T00:00:00Z", f"{QUERY_END_DATE}T23:59:59Z"),
                        maxcc=0.8,
                        mosaicking_order=MosaickingOrder.MOST_RECENT,
                    )
                ],
                responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
                bbox=BBox(bbox=region_bbox, crs=CRS.WGS84),
                size=[width, height],
                config=sh_config,
            )

        region_results = []
        for region in region_requests:
            request = build_request(EVALSCRIPT, region["bbox"], region["width"], region["height"])
            response = request.get_data(save_data=False)
            mask = response[0].astype(np.uint8)
            region_results.append(
                {
                    "name": region["name"],
                    "bbox": region["bbox"],
                    "mask": mask,
                    "width": region["width"],
                    "height": region["height"],
                }
            )

    all_coordinates = []
    total_positive_pixels = 0
    for region_result in region_results:
        region_mask = region_result["mask"]
        total_positive_pixels += int(np.count_nonzero(region_mask == 1))
        region_coordinates = extract_relevant_coordinates(
            region_mask,
            region_result["bbox"],
            min_component_pixels=MIN_COMPONENT_PIXELS,
            max_relevant_points=MAX_RELEVANT_POINTS,
        )
        print(
            f"Region {region_result['name']}: {len(region_coordinates)} centroid points "
            f"from {int(np.count_nonzero(region_mask == 1))} positive pixels"
        )
        all_coordinates.extend(region_coordinates)

    # Deduplicate nearby identical centroids after multi-region merge.
    coordinates = list(dict.fromkeys((round(lat, 6), round(lon, 6)) for lat, lon in all_coordinates))
    print(f"Total mask positive pixels: {total_positive_pixels}")
    print(f"Relevant centroid points after merge: {len(coordinates)}")

    db = SessionLocal()
    
    # Force Python to see the backend directory before importing
    import sys
    sys.path.insert(0, str(ROOT_DIR / "backend"))
    from app.db.models import PlasticDebris, User, Notification

    from geoalchemy2.types import Geography
    from sqlalchemy import cast

    # 1. VERIFICARE PUNCTE COLECTATE (care așteaptă confirmarea satelitului)
    # Extragem direct lon și lat folosind funcțiile spațiale din baza de date
    pending_debris = db.query(
        PlasticDebris,
        func.ST_X(PlasticDebris.geom).label("lon"),
        func.ST_Y(PlasticDebris.geom).label("lat")
    ).filter(
        PlasticDebris.is_collected == True,
        PlasticDebris.is_verified == False,
        PlasticDebris.size_category != "beach" # Doar cele din ocean au nevoie de satelit
    ).all()

    verified_count = 0
    for debris, lon, lat in pending_debris:
        for region_result in region_results:
            min_lon, min_lat, max_lon, max_lat = region_result["bbox"]
            region_mask = region_result["mask"]
            height, width = region_mask.shape

            # Verificăm dacă punctul se află într-un BBOX curent de satelit
            if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
                continue

            lon_fraction = (lon - min_lon) / (max_lon - min_lon)
            lat_fraction = (lat - min_lat) / (max_lat - min_lat)
            col = min(width - 1, max(0, int(round(lon_fraction * width))))
            row = min(height - 1, max(0, int(round((1.0 - lat_fraction) * height))))

            # Dacă satelitul vede APĂ CURATĂ (0) unde înainte era gunoi, confirmăm curățarea!
            if region_mask[row, col] == 0:
                debris.is_verified = True
                user = db.query(User).filter(User.id == debris.collected_by).first()
                if user:
                    user.eco_points += debris.eco_points
                    # Notificăm utilizatorul că a primit punctele!
                    notif = Notification(
                        user_id=user.id,
                        message=f"🛰️ Satelitul a confirmat curățarea deșeului #{debris.id}! "
                                f"Ai primit {debris.eco_points} puncte eco. Mulțumim!"
                    )
                    db.add(notif)
                verified_count += 1
            break

    # 2. INSERARE PUNCTE NOI DETECTATE (Fără a crea duplicate)
    inserted_count = 0
    for lat, lon in coordinates:
        point = WKTElement(f"SRID=4326;POINT({lon} {lat})")
        
        # Verificăm dacă există deja un deșeu NECOLECTAT foarte aproape (raza 100m)
        existing = db.query(PlasticDebris).filter(
            PlasticDebris.is_collected == False,
            func.ST_DWithin(cast(PlasticDebris.geom, Geography), cast(point, Geography), 100)
        ).first()

        if not existing:
            new_debris = PlasticDebris(
                geom=point,
                size_category="small",
                detected_at=datetime.now(timezone.utc),
                is_collected=False,
                is_verified=False,
                eco_points=5,
            )
            db.add(new_debris)
            inserted_count += 1

    db.commit()
    db.close()

    print(f"Satellite sync complete: {inserted_count} new debris inserted, {verified_count} debris cleanups verified.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and process Sentinel debris detections")
    parser.add_argument(
        "--tuning-help",
        action="store_true",
        help="Print a practical guide for tuning bbox/grid and detection variables",
    )
    args = parser.parse_args()

    if args.tuning_help:
        print_tuning_help()
    else:
        fetch_and_process()

#  USE_PRESET_LOCATIONS=true PRESET_LOCATION_SET=world_hotspots TARGET_RESOLUTION_METERS=10 MIN_COMPONENT_PIXELS=12 MAX_RELEVANT_POINTS=1200 /home/rares/anaconda3/bin/conda run -p /mnt/Storage/PlasticPatrol/PlasticPatrol/.conda --no-capture-output python /home/rares/.vscode/extensions/ms-python.python-2026.4.0-linux-x64/python_files/get_output_via_markers.py data_pipeline/sentinel_fetcher.py
# 
# 
# 
# 