import httpx

codes = ['5701929', '2001020', '2001500', '2000172', '2000296']
for code in codes:
    r = httpx.get(f'https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{code}', timeout=10.0)
    data = r.json()
    print(f"CNES {code}: {data.get('nome_razao_social')} | codigo_cnes retornado: {data.get('codigo_cnes')}")