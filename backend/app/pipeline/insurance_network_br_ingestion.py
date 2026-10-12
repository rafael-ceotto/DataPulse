import csv, io, os, tempfile, zipfile
from httpx import AsyncClient, Timeout
from app.core.config import settings
from app.schemas.insurance_br import HospitalInsuranceNetworkEntry

async def download_ans_zip() -> str:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_fd)
    try:
        timeout = Timeout(connect=30.0, read=300.0, write=300.0, pool=30.0)
        headers = {"User-Agent": "Mozilla/5.0 (DataPulse ingestion bot)"}
        async with AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            async with client.stream("GET", settings.ANS_INSURANCE_NETWORK_URL) as response:
                response.raise_for_status()
                with open(tmp_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
        return tmp_path
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def parse_state_csv(zf: zipfile.ZipFile, entry_name: str, cnes_to_facility_id: dict[str, str],
) -> dict[tuple[str, str], HospitalInsuranceNetworkEntry]:
    
    dedup: dict[tuple[str, str], HospitalInsuranceNetworkEntry] = {}

    with zf.open(entry_name) as f:
        text_stream = io.TextIOWrapper(f, encoding="latin-1")
        reader = csv.DictReader(text_stream, delimiter=";")

        for row in reader:
            cnes = row.get("CD_CNES", "")
            facility_id = cnes_to_facility_id.get(cnes)
            if facility_id is None:
                continue

            operator_code = row.get("CD_OPERADORA", "")
            key = (facility_id, operator_code)
            is_active = row.get("DT_VINCULO_FIM", "") == ""

            existing = dedup.get(key)
            if existing is not None and existing.is_active and not is_active:
                continue  

            dedup[key] = HospitalInsuranceNetworkEntry(
                facility_id=facility_id,
                operator_code=operator_code,
                operator_name=row.get("NO_RAZAO"),
                has_emergency_coverage=row.get("LG_URGENCIA_EMERGENCIA", "0"),
                coverage_type=row.get("SEGMENTACAO_ASSISTENCIAL"),
                provider_relationship=row.get("DE_TIPO_PRESTADOR"),
                is_active=is_active,
            )

    return dedup

