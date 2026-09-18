from pydantic import BaseModel, field_validator
from typing import Any
from app.core.logging import logger


class AgentOutput(BaseModel):
    question: str
    mode: str
    tools_used: list[str]
    explanation: str
    results: list[Any]
    tokens_used: dict | None = None
    estimated_cost_usd: float | None = None

    @field_validator("explanation")
    @classmethod
    def explanation_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("explanation cannot be empty")
        return v


def validate_agent_output(data: dict) -> dict:
    try:
        validated = AgentOutput(**data)
        return validated.model_dump()
    except Exception as e:
        logger.error("agent_output_validation_failed", error=str(e), data=str(data)[:200])
        raise ValueError(f"Agent output validation failed: {e}")