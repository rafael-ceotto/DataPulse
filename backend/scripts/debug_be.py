import httpx
import json

query = """
SELECT ?hospital ?hospitalLabel ?cityLabel ?lat ?lng WHERE {
  ?hospital wdt:P31 wd:Q16917.
  ?hospital wdt:P17 wd:Q31.
  ?hospital wdt:P625 ?coords.
  BIND(geof:latitude(?coords) AS ?lat)
  BIND(geof:longitude(?coords) AS ?lng)
  OPTIONAL { ?hospital wdt:P131 ?city. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,nl,en". }
}
LIMIT 5
"""

r = httpx.get(
    'https://query.wikidata.org/sparql',
    params={'query': query, 'format': 'json'},
    timeout=30.0,
    headers={'User-Agent': 'DataPulse/1.0'}
)
data = r.json()
results = data.get('results', {}).get('bindings', [])
for item in results:
    print(f"hospital: {item.get('hospital',{}).get('value','').split('/')[-1]}")
    print(f"hospitalLabel: {item.get('hospitalLabel',{}).get('value','')}")
    print(f"cityLabel: {item.get('cityLabel',{}).get('value','')}")
    print('---')