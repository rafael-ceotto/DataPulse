import asyncio
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from app.core.s3 import list_objects, download_file
from app.rag.ingestion import ingest_all_pdfs


async def main():
    print("Fetching CMS PDFs from S3...")

    pdf_keys = await list_objects("cms-docs/")
    pdf_keys = [k for k in pdf_keys if k.endswith(".pdf")]

    if not pdf_keys:
        print("No PDFs found in s3://datapulse/cms-docs/")
        print("Run: poetry run python scripts/upload_cms_docs_to_s3.py first")
        return

    print(f"Found {len(pdf_keys)} PDFs in S3. Downloading...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        for key in pdf_keys:
            filename = os.path.basename(key)
            destination = os.path.join(tmp_dir, filename)
            await download_file(key, destination)

        print(f"\nIngesting {len(pdf_keys)} PDFs...")
        async with AsyncSessionLocal() as session:
            results = await ingest_all_pdfs(tmp_dir, session)

    if not results:
        print("No PDFs processed.")
        return

    print("\nIngestion complete:")
    for filename, count in results.items():
        print(f"  {filename}: {count} chunks")

    total = sum(results.values())
    print(f"\nTotal: {total} chunks indexed")


if __name__ == "__main__":
    asyncio.run(main())