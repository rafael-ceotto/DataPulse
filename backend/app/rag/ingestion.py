import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models.document_chunk import DocumentChunk
from app.rag.chunker import extract_chunks
from app.rag.embeddings import embed_text

async def ingest_pdf(pdf_path: str, session: AsyncSession) -> int:
    print(f"Ingest {pdf_path}")
    
    #Get rid of existing chunks for this source
    await session.execute(delete(DocumentChunk).where(DocumentChunk.source == pdf_path))
    #Extract chunks from PDF
    chunks = extract_chunks(pdf_path)
    if not chunks:
       print(f"No chunks extracted from {pdf_path}")
       return 0 
    print(f"Extracted {len(chunks)} chunks, generating embeddings...")
    # Embeddings in batch generation
    texts = [c["content"] for c in chunks]
    embeddings = embed_text(texts)
    #Save to DB
    db_chunks = [
        DocumentChunk(
            source = os.path.basename(pdf_path),
            page = chunk["page"],
            content=chunk["content"],
            embedding = embedding,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    
    session.add_all(db_chunks)
    await session.commit()
    print(f"Saved {len(db_chunks)} chunks from {pdf_path}")
    return len(db_chunks)

async def ingest_all_pdfs(pdf_dir: str, session: AsyncSession) -> dict:
    results = {}
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
       print(f"No PDF files found in {pdf_dir}")
       return results 
    
    for filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, filename)
        count = await ingest_pdf(pdf_path, session)
        results[filename] = count
        
    return results