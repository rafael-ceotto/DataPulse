import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.s3 import upload_file, list_objects

CMS_DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cms_docs"))


async def main():
    if not os.path.exists(CMS_DOCS_DIR):
        print(f"Directory not found: {CMS_DOCS_DIR}")
        return

    pdf_files = [f for f in os.listdir(CMS_DOCS_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in cms_docs/")
        return

    print(f"Found {len(pdf_files)} PDFs. Uploading to S3...")

    for filename in pdf_files:
        file_path = os.path.join(CMS_DOCS_DIR, filename)
        s3_key = f"cms-docs/{filename}"
        await upload_file(s3_key, file_path)

    print("\nVerifying upload...")
    objects = await list_objects("cms-docs/")
    for key in objects:
        print(f"  s3://datapulse/{key}")

    print(f"\nDone. {len(objects)} PDFs in S3.")


if __name__ == "__main__":
    asyncio.run(main())