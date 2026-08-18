import httpx

URL = "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1785189955/Hospital_General_Information.csv"

async def fetch_data_cms():
    try:
        async with httpx.AsyncClient() as client:
            response =  await client.get(URL)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        print(f"Couldn't retrieve data from CMS: {e}")
        return None
    
    
import asyncio

if __name__ == "__main__":
    result = asyncio.run(fetch_data_cms())
    if result:
        lines = result.split("\n")
        for line in lines[:3]:
            print(line)