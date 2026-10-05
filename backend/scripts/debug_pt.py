import httpx

query = """
SELECT (COUNT(*) AS ?count) WHERE {
  ?hospital wdt:P31 wd:Q16917.
  ?hospital wdt:P17 wd:Q45.
  ?hospital wdt:P625 ?coords.
}
"""

r = httpx.get(
    'https://query.wikidata.org/sparql',
    params={'query': query, 'format': 'json'},
    timeout=30.0,
    headers={'User-Agent': 'DataPulse/1.0'}
)
data = r.json()
count = data.get('results', {}).get('bindings', [{}])[0].get('count', {}).get('value', '?')
print(f'Total Portuguese hospitals with coordinates: {count}')