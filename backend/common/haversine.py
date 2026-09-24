"""
Haversine distance calculation for SONAR-X geospatial operations.
Uses WGS84 Earth radius.
"""

import math


EARTH_RADIUS_M = 6_371_000.0  # metres


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Parameters
    ----------
    lat1, lon1 : float — first point (decimal degrees WGS84)
    lat2, lon2 : float — second point (decimal degrees WGS84)

    Returns
    -------
    float — distance in metres
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial bearing from point 1 to point 2.

    Returns
    -------
    float — bearing in degrees (0–360, clockwise from North)
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lam = math.radians(lon2 - lon1)

    x = math.sin(d_lam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lam)

    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360
