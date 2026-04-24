import numpy as np
import os
from datetime import datetime, timezone
from sentinelhub import SentinelHubRequest, MimeType, CRS, BBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.elements import WKTElement
from shapely.geometry import Point

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@localhost:5432/plasticpatrol")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sentinel Hub API key (set via environment variable)
SENTINEL_HUB_API_KEY = os.getenv("SENTINEL_HUB_API_KEY", "YOUR_API_KEY_HERE")

# Custom Evalscript for Floating Debris Index (FDI) using NDVI as proxy
EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B2", "B3", "B4", "B8"],
    output: { bands: 1, sampleType: "UINT8" }
  };
}

function evaluatePixel(sample) {
  // NDVI = (NIR - RED) / (NIR + RED)
  // B4 = RED, B8 = NIR
  let numerator = sample.B8 - sample.B4;
  let denominator = sample.B8 + sample.B4;
  let ndvi = 0;
  
  if (denominator !== 0) {
    ndvi = numerator / denominator;
  }
  
  // Heuristic: pixels with negative or very low NDVI (water/debris)
  // and certain spectral characteristics indicate potential debris
  // Return 1 if likely debris, 0 if likely water
  if (ndvi < 0.1 && sample.B2 < 500 && sample.B3 < 400) {
    return [1];
  }
  return [0];
}
"""

# Bounding box over Mediterranean Sea (coastal region)
# Coordinates: [min_lon, min_lat, max_lon, max_lat]
BBOX_COORDS = [13.0, 37.0, 15.0, 39.0]  # Area around Sicily/Malta
bbox = BBox(bbox=BBOX_COORDS, crs=CRS.WGS84)

# Date for query (use recent date)
QUERY_DATE = "2024-04-10"

def extract_coordinates_from_mask(mask, bbox_coords):
    """
    Extract geographic coordinates from binary mask array.
    
    Args:
        mask: NumPy array with binary values (1 = debris, 0 = water)
        bbox_coords: [min_lon, min_lat, max_lon, max_lat]
    
    Returns:
        List of (lon, lat) tuples
    """
    debris_indices = np.argwhere(mask == 1)
    
    min_lon, min_lat, max_lon, max_lat = bbox_coords
    
    # Get array dimensions
    height, width = mask.shape
    
    coordinates = []
    for row, col in debris_indices:
        # Normalize pixel coordinates to [0, 1]
        lat_fraction = 1.0 - (row / height)  # Flip because array index increases downward
        lon_fraction = col / width
        
        # Convert to geographic coordinates
        lon = min_lon + lon_fraction * (max_lon - min_lon)
        lat = min_lat + lat_fraction * (max_lat - min_lat)
        
        coordinates.append((lon, lat))
    
    return coordinates

def fetch_and_process():
    """
    Fetch Sentinel-2 data from Sentinel Hub, process mask, and insert into database.
    """
    # Create Sentinel Hub request
    request = SentinelHubRequest(
        evalscript=EVALSCRIPT,
        input_data=[
            {
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{QUERY_DATE}T00:00:00Z",
                        "to": f"{QUERY_DATE}T23:59:59Z"
                    }
                },
                "processing": {}
            }
        ],
        responses=[
            {
                "identifier": "default",
                "format": {
                    "type": "image/tiff"
                }
            }
        ],
        bbox=bbox,
        size=[512, 512],  # Resolution: 512x512 pixels
        config={"sh_client_id": "", "sh_client_secret": SENTINEL_HUB_API_KEY}
    )
    
    # Execute request and get response data
    response = request.get_data(save_data=False)
    
    # Extract first (and only) response as NumPy array
    mask = response[0].astype(np.uint8)
    
    # Extract debris coordinates from mask
    coordinates = extract_coordinates_from_mask(mask, BBOX_COORDS)
    
    # Open database session
    db = SessionLocal()
    
    # Import PlasticDebris model
    from app.db.models import PlasticDebris
    
    # Create and insert PlasticDebris objects
    for lon, lat in coordinates:
        # Create WKT POINT geometry in EPSG:4326
        point = WKTElement(f'SRID=4326;POINT({lon} {lat})')
        
        debris = PlasticDebris(
            geom=point,
            size_category="small",
            detected_at=datetime.now(timezone.utc),
            is_collected=False,
            eco_points=5
        )
        db.add(debris)
    
    # Commit all changes
    db.commit()
    db.close()
    
    print(f"Inserted {len(coordinates)} debris points into database")

if __name__ == "__main__":
    fetch_and_process()
