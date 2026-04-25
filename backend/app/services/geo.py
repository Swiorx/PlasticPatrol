import math


def meters_per_degree_lon(lat_deg: float) -> float:
    return 111320.0 * max(0.1, math.cos(math.radians(lat_deg)))


def bbox_for_user(latitude: float, longitude: float, radius_km: float = 12.0) -> list[float]:
    """Return [min_lon, min_lat, max_lon, max_lat] of a square ~2*radius_km wide centered on (lat, lon)."""
    radius_m = radius_km * 1000.0
    dlat = radius_m / 111320.0
    dlon = radius_m / meters_per_degree_lon(latitude)

    min_lat = max(-90.0, latitude - dlat)
    max_lat = min(90.0, latitude + dlat)
    min_lon = max(-180.0, longitude - dlon)
    max_lon = min(180.0, longitude + dlon)
    return [min_lon, min_lat, max_lon, max_lat]
