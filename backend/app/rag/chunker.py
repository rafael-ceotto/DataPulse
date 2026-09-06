from pypdf import PdfReader


def extract_chunks(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    reader = PdfReader(pdf_path)
    chunks = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        text = _clean(text)
        page_chunks = _split(text, chunk_size, overlap)

        for chunk in page_chunks:
            if len(chunk.strip()) < 50:
                continue
            chunks.append({
                "source": pdf_path,
                "page": page_num,
                "content": chunk.strip(),
            })

    return chunks


def _clean(text: str) -> str:
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    return text.strip()


def _split(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            boundary = text.rfind(' ', start, end)
            if boundary > start:
                end = boundary

        chunks.append(text[start:end])
        start = end - overlap

    return chunks