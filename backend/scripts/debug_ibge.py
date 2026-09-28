import httpx

r = httpx.get('https://servicodados.ibge.gov.br/api/v1/localidades/municipios', timeout=30.0)
data = r.json()
print(f'Total municipios: {len(data)}')
print(f'Sample ID: {data[0]["id"]}')
print(f'Sample nome: {data[0]["nome"]}')

sample_id = str(data[0]["id"])
print(f'6 digits: {sample_id[:6]}')