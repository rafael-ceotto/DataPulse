from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.rag.embeddings import embed_text


async def search_documents(query: str, session: AsyncSession, top_k: int = 5) -> list[dict]:
    query_embedding = embed_text(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    result = await session.execute(
        text(f"""
            SELECT
                source,
                page,
                content,
                1 - (embedding <=> '{embedding_str}'::vector) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :top_k
        """),
        {"top_k": top_k}
    )

    rows = result.fetchall()

    return [
        {
            "source": row.source,
            "page": row.page,
            "content": row.content,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]