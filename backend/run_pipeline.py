import asyncio
from app.core.database import AsyncSessionLocal
from app.services.hospital_service import ingest_hospitals

async def run():
    try:
        async with AsyncSessionLocal() as session:
            result = await ingest_hospitals(session)
            print(f'Done: {result} hospitals')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'Error: {e}')

asyncio.run(run())
