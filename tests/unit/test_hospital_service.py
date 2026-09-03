import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.hospital_service import ingest_hospitals

MOCK_CSV = """Facility ID,Facility Name,Address,City/Town,State,ZIP Code,County/Parish,Telephone Number,Hospital Type,Hospital Ownership,Emergency Services,Meets criteria for birthing friendly designation,Hospital overall rating,...
010001,Test Hospital,123 Main St,Boston,MA,02108,Suffolk,555-1234,Acute Care Hospitals,Voluntary non-profit - Private,Yes,,4,...
010002,Another Hospital,456 Oak Ave,Cambridge,MA,02139,Middlesex,555-5678,Acute Care Hospitals,Voluntary non-profit - Private,Yes,,3,..."""

@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_ingest_hospital_success(mock_session):
    mock_pipeline_run = MagicMock()
    mock_pipeline_run.id = "test-uuid"
    
    with patch("app.services.hospital_service.fetch_data_cms", new=AsyncMock(return_value=MOCK_CSV)), \
         patch("app.services.hospital_service.save_hospitals", new=AsyncMock()), \
         patch("app.services.hospital_service.create_pipeline_run", new=AsyncMock(return_value=mock_pipeline_run)), \
         patch("app.services.hospital_service.update_pipeline_run", new=AsyncMock()), \
         patch("app.services.hospital_service.get_previous_avg_rating", new=AsyncMock(return_value=3.5)), \
         patch("app.services.hospital_service.get_recent_insights", new=AsyncMock(return_value=[])), \
         patch("app.services.hospital_service.generate_insight", new=AsyncMock(return_value="Test insight")), \
         patch("app.services.hospital_service.send_slack_alert", new=AsyncMock()), \
         patch("app.services.hospital_service.commit_insight", new=AsyncMock()):
        
        result = await ingest_hospitals(mock_session)
        assert result == 2
        
@pytest.mark.asyncio
async def test_ingest_hospitals_fetch_fails(mock_session):
    mock_pipeline_run = MagicMock()

    with patch("app.services.hospital_service.fetch_data_cms", new=AsyncMock(return_value=None)), \
         patch("app.services.hospital_service.create_pipeline_run", new=AsyncMock(return_value=mock_pipeline_run)), \
         patch("app.services.hospital_service.update_pipeline_run", new=AsyncMock()):

        with pytest.raises(ValueError, match="Failed to fetch data from CMS"):
            await ingest_hospitals(mock_session)
            
@pytest.mark.asyncio
async def test_ingest_hospitals_calculates_avg_rating(mock_session):
    mock_pipeline_run = MagicMock()
    captured = {}

    async def mock_update(session, run, status, records_received, records_processed, records_failed, avg_rating=None, insight=None, error_message=None):
        captured["avg_rating"] = avg_rating
        captured["status"] = status

    with patch("app.services.hospital_service.fetch_data_cms", new=AsyncMock(return_value=MOCK_CSV)), \
         patch("app.services.hospital_service.save_hospitals", new=AsyncMock()), \
         patch("app.services.hospital_service.create_pipeline_run", new=AsyncMock(return_value=mock_pipeline_run)), \
         patch("app.services.hospital_service.update_pipeline_run", new=mock_update), \
         patch("app.services.hospital_service.get_previous_avg_rating", new=AsyncMock(return_value=None)), \
         patch("app.services.hospital_service.get_recent_insights", new=AsyncMock(return_value=[])), \
         patch("app.services.hospital_service.generate_insight", new=AsyncMock(return_value="Test insight")), \
         patch("app.services.hospital_service.send_slack_alert", new=AsyncMock()), \
         patch("app.services.hospital_service.commit_insight", new=AsyncMock()):

        await ingest_hospitals(mock_session)
        assert captured["avg_rating"] == 3.5  # (4 + 3) / 2
        assert captured["status"] == "success"
        
@pytest.mark.asyncio
async def test_ingest_hospitals_insight_failure_does_not_break_pipeline(mock_session):
    mock_pipeline_run = MagicMock()

    with patch("app.services.hospital_service.fetch_data_cms", new=AsyncMock(return_value=MOCK_CSV)), \
         patch("app.services.hospital_service.save_hospitals", new=AsyncMock()), \
         patch("app.services.hospital_service.create_pipeline_run", new=AsyncMock(return_value=mock_pipeline_run)), \
         patch("app.services.hospital_service.update_pipeline_run", new=AsyncMock()), \
         patch("app.services.hospital_service.get_previous_avg_rating", new=AsyncMock(return_value=None)), \
         patch("app.services.hospital_service.get_recent_insights", new=AsyncMock(return_value=[])), \
         patch("app.services.hospital_service.generate_insight", new=AsyncMock(side_effect=Exception("Groq error"))), \
         patch("app.services.hospital_service.send_slack_alert", new=AsyncMock()), \
         patch("app.services.hospital_service.commit_insight", new=AsyncMock()):

        result = await ingest_hospitals(mock_session)
        assert result == 2
