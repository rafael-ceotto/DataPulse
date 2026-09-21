import httpx
import csv
import io
import json
from app.core.logging import logger

URL = "https://gist.github.com/abatko/94d1fa8e76a3b7ce98ff8e6178c97861/raw"

def download_zip_lat_lng() -> dict[str, tuple[float, float]]:
    #Download ZIP code lat/lng lookup table
    r = httpx.get(URL, timeout=30.0, follow_redirects=True)
    r.raise_for_status()
    
    lookup = {}
    reader = csv. DictReader(io.StringIO(r.text), delimiter="\t")
    for row in reader:
        zip_code = row["ZIP"].strip().zfill(5)
        try:
            lat = float(row["LAT"])
            lng = float(row["LNG"])
            lookup[zip_code] = (lat, lng)
        except (ValueError, KeyError):
            continue
    logger.info("zip_lookup_loaded", count=len(lookup))
    return lookup

if __name__ == "__main__":
    lookup =  download_zip_lat_lng()
    with open("zip_lat_lng.json", "w") as f:
        json.dump({k: list(v) for k, v in lookup.items()}, f)
    logger.info("zip_lookup_saved", file="zip_lat_lng.json")
    logger.info("zip_sample_10001", coords=lookup.get("10001"))
    logger.info("zip_sample_90210", coords=lookup.get("90210"))