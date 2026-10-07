import httpx
import time

hospitals = [
    {"name": "St. Luke's Hospital, Malta", "lat": 35.893433333, "lon": 14.494183333},
    {"name": "St James Capua Hospital", "lat": 35.9131, "lon": 14.5033},
    {"name": "St Philip's Hospital", "lat": 35.893056, "lon": 14.482222},
    {"name": "Villa St Ignatius", "lat": 35.9137, "lon": 14.4955},
    {"name": "Old Hospital, Mqabba", "lat": 35.844, "lon": 14.46733},
]

for h in hospitals:
    time.sleep(1.1)
    r = httpx.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={"lat": h["lat"], "lon": h["lon"], "format": "json", "addressdetails": 1},
        timeout=15.0,
        headers={"User-Agent": "DataPulse/1.0"},
    )
    data = r.json()
    address = data.get("address", {})
    road = address.get("road") or address.get("pedestrian")
    postcode = address.get("postcode")
    city = address.get("city") or address.get("town") or address.get("village") or address.get("suburb")
    print(f"{h['name']} -> road={road}, postcode={postcode}, city={city}")