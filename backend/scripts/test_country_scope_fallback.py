import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.hospital_ai_service import ask_hospital_ai
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        print("=== Case 1: in-scope question, country=BR ===")
        result = await ask_hospital_ai(session, "Quais os hospitais mais bem avaliados?", country="BR")
        print("SQL:", result["sql"])
        print("Explanation:", result["explanation"])
        assert "country" in result["sql"].lower() or result["sql"] == "", (
            "Expected the generated SQL to filter by country, or be empty."
        )
        if result["sql"]:
            assert "'br'" in result["sql"].lower(), "Expected filter on country = 'BR'."
        print()

        print("=== Case 2: explicit wrong-country question, country=BR ===")
        result = await ask_hospital_ai(
            session,
            "Quais os hospitais mais bem avaliados nos Estados Unidos?",
            country="BR",
        )
        print("SQL:", result["sql"])
        print("Explanation:", result["explanation"])
        assert result["sql"] == "", "Expected an empty SQL (refusal) for an out-of-scope country question."

    print("\nPASSED: country scoping behaved as expected.")


if __name__ == "__main__":
    asyncio.run(main())