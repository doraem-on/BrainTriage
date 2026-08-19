"""Nearby-care lookup and emergency numbers.

Hospital search uses OpenStreetMap's free, keyless public services —
Nominatim (geocoding) and Overpass (POI queries) — rather than a paid Maps
API, so this works with zero configuration. Per OSM's usage policy this
requires a descriptive User-Agent and reasonable request rates; there's no
API key to manage or leak.

Emergency numbers are a small, hand-curated static table, not fetched from
anywhere — only widely-documented national emergency numbers are included
with high confidence; anything more specific (NGO helplines) is marked
"verify locally" rather than asserted as certainly current.
"""
import math

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/locations", tags=["locations"])

USER_AGENT = "BrainTriage/1.0 (hackathon prototype; contact via project repo)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/geocode")
def geocode(q: str = Query(..., min_length=2)):
    """Turn a free-text place/city/address into lat/lon candidates."""
    try:
        resp = httpx.get(
            NOMINATIM_URL,
            params={"q": q, "format": "json", "limit": 5},
            headers={"User-Agent": USER_AGENT},
            timeout=10.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Geocoding service unavailable: {e}")

    return [
        {"display_name": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"])}
        for r in resp.json()
    ]


@router.get("/hospitals")
def nearby_hospitals(lat: float, lon: float, radius_km: float = 15.0):
    """Real hospitals/clinics near a point, via OpenStreetMap Overpass."""
    radius_m = int(min(radius_km, 50) * 1000)  # cap radius to keep queries fast
    overpass_query = f"""
    [out:json][timeout:20];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
      node["healthcare"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center 40;
    """
    try:
        resp = httpx.post(
            OVERPASS_URL,
            data={"data": overpass_query},
            headers={"User-Agent": USER_AGENT},
            timeout=25.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Hospital lookup service unavailable: {e}")

    elements = resp.json().get("elements", [])
    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        el_lat = el.get("lat") or el.get("center", {}).get("lat")
        el_lon = el.get("lon") or el.get("center", {}).get("lon")
        if el_lat is None or el_lon is None:
            continue
        address_parts = [
            tags.get("addr:housenumber"), tags.get("addr:street"),
            tags.get("addr:city"), tags.get("addr:postcode"),
        ]
        address = ", ".join(p for p in address_parts if p)
        results.append({
            "name": name,
            "address": address or None,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "emergency": tags.get("emergency") == "yes",
            "lat": el_lat,
            "lon": el_lon,
            "distance_km": round(_haversine_km(lat, lon, el_lat, el_lon), 1),
        })

    results.sort(key=lambda r: r["distance_km"])
    return results[:25]


# Only widely-documented national emergency numbers are asserted with
# confidence. Country-specific helplines are marked for local verification.
EMERGENCY_NUMBERS = {
    "IN": {
        "country": "India",
        "general": [
            {"label": "National Emergency (police / fire / ambulance)", "number": "112"},
            {"label": "Police", "number": "100"},
            {"label": "Ambulance", "number": "102 / 108"},
            {"label": "Women's Helpline", "number": "1091"},
            {"label": "National Elder Helpline (Senior Citizens)", "number": "14567"},
        ],
        "dementia_specific": [
            {"label": "ARDSI (Alzheimer's & Related Disorders Society of India) — commonly published national helpline", "number": "1800-180-1980", "verify": True},
        ],
    },
    "US": {
        "country": "United States",
        "general": [{"label": "Emergency (police / fire / ambulance)", "number": "911"}],
        "dementia_specific": [
            {"label": "Alzheimer's Association 24/7 Helpline", "number": "1-800-272-3900", "verify": True},
        ],
    },
    "UK": {
        "country": "United Kingdom",
        "general": [
            {"label": "Emergency (police / fire / ambulance)", "number": "999"},
            {"label": "Non-emergency medical (NHS)", "number": "111"},
        ],
        "dementia_specific": [
            {"label": "Alzheimer's Society Dementia Connect", "number": "0333 150 3456", "verify": True},
        ],
    },
    "CA": {
        "country": "Canada",
        "general": [{"label": "Emergency (police / fire / ambulance)", "number": "911"}],
        "dementia_specific": [],
    },
    "AU": {
        "country": "Australia",
        "general": [{"label": "Emergency (police / fire / ambulance)", "number": "000"}],
        "dementia_specific": [
            {"label": "Dementia Australia National Helpline", "number": "1800 100 500", "verify": True},
        ],
    },
    "EU": {
        "country": "European Union (general)",
        "general": [{"label": "EU-wide Emergency Number", "number": "112"}],
        "dementia_specific": [],
    },
}


@router.get("/emergency-numbers")
def emergency_numbers():
    return {
        "disclaimer": "Numbers change over time and vary by state/region — verify locally before relying on any number in a genuine emergency. Rows marked verify=true are commonly published helpline numbers we have lower confidence in.",
        "countries": EMERGENCY_NUMBERS,
        "default": "IN",
    }
