import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from app.rag.ingestion import ingest_all_pdfs

async def main():
    pdf_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cms_docs")
    pdf_dir = os.path.abspath(pdf_dir)
    
    if not os.path.exists(pdf_dir):
        print(f"Directory not found: {pdf_dir}")
        return
    print(f"Scanning {pdf_dir}...")
    
    async with AsyncSessionLocal() as session:
        results = await ingest_all_pdfs(pdf_dir, session)
        
    if not results:
        print("No PDFs processed.")
        return
    
    print("\nIngestion complete: ")
    for filename, count in results.items():
        print(f" {filename}: {count} chunks")
        
    total = sum(results.values())
    print(f"\nTotal: {total} chunks indexed")
    
if __name__ == "__main__":
    asyncio.run(main())