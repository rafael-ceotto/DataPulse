import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from app.rag.retriever import search_documents

async def main():
    query = "What are the criteria for a hospital to receive a 5-star rating?"
    
    async with AsyncSessionLocal() as session:
        results = await search_documents(query, session, top_k=3)
        
    print(f"Query: {query}\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"Source: {r['source']}, Page: {r['page']}, Similarity: {r['similarity']}")
        print(f"Content: {r['content'][:300]}")
        print()
        
if __name__ == "__main__":
    asyncio.run(main())