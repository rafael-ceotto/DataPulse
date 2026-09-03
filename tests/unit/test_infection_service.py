import pytest
from unittest.mock import AsyncMock, patch
from app.services.infection_service import ingest_infections

MOCK_CSV = """Facility ID,Facility Name,State,Measure ID,Measure Name,Compared to National,Score,Footnote,Start Date,End Date
010001,Test Hospital,AL,HAI_1_SIR,CLABSI,No Different than the National Benchmark,0.5,,01/01/2023,12/31/2023
010002,Another Hospital,AL,HAI_2_SIR,CAUTI,Better than the National Benchmark,0.3,,01/01/2023,12/31/2023"""

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_ingestion_success(mock_session):
    with patch("app.services.infection_service.fetch_infections_cms", new=AsyncMock(return_value=MOCK_CSV)), \
         patch("app.services.infection_service.parse_infections", return_value=[object(), object()]), \
         patch("app.services.infection_service.save_infections", new=AsyncMock()):
             result = await ingest_infections(mock_session)
             assert result == 2
             
@pytest.mark.asyncio
async def test_ingest_infections_fetch_fails(mock_session):
    with patch("app.services.infection_service.fetch_infections_cms", new=AsyncMock(return_value=None)):
        with pytest.raises(ValueError, match="Failed to fetch infection data from CMS"):
            await ingest_infections(mock_session)
            
@pytest.mark.asyncio
async def test_ingest_infections_empty_csv(mock_session):
    with patch("app.services.infection_service.fetch_infections_cms", new=AsyncMock(return_value=MOCK_CSV)), \
         patch("app.services.infection_service.parse_infections", return_value=[]), \
         patch("app.services.infection_service.save_infections", new=AsyncMock()):

        result = await ingest_infections(mock_session)
        assert result == 0