import httpx
import csv
import io

# Geolocated file
r = httpx.get(
    'https://static.data.gouv.fr/resources/finess-extraction-du-fichier-des-etablissements/20260512-091152/etalab-cs1100507-stock-20260512-0339.csv',
    timeout=30.0,
    follow_redirects=True
)
lines = r.text.split('\n')
reader = csv.reader(io.StringIO('\n'.join(lines[1:])), delimiter=';')

count = 0
for row in reader:
    if len(row) < 20:
        continue
    code_type = row[18]
    if code_type in ['355', '101', '106']:
        print(f"Total fields: {len(row)}")
        for i, val in enumerate(row):
            print(f"  [{i}]: {val}")
        count += 1
        if count >= 2:
            break