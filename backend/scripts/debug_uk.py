import httpx
import json

r = httpx.post(
    'https://api.postcodes.io/postcodes',
    json={'postcodes': ['NW1 0PE', 'SW1A 1AA', 'E1 6AN']},
    timeout=10.0
)
print('Status:', r.status_code)
data = r.json()
for item in data.get('result', []):
    res = item.get('result', {})
    print(f"{item['query']}: lat={res.get('latitude')}, lng={res.get('longitude')}, city={res.get('admin_district')}")