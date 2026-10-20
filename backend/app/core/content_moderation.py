# PII redaction via regex - deterministic, local, no extra call
# Harmfull-content classification via Llama Guard (meta-llama/llama-guard-4-12b)

import json
import re

import httpx

from app.core.config import settings
from app.core.logging import logger

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SAFETY_MODEL = "openai/gpt-oss-safeguard-20b"

SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?(?:\(\d{2,3}\)[ -]?)?\d{4,5}[ -]?\d{4}\b")

# Order matters: more specific patterns (SSN, CPF, credit card) run before
# the broad phone-number pattern, which would otherwise also match them.
PII_PATTERNS = (
    ("ssn", SSN_RE),
    ("cpf", CPF_RE),
    ("credit_card", CREDIT_CARD_RE),
    ("email", EMAIL_RE),
    ("phone", PHONE_RE),
)

# Policy for the gpt-oss-safeguard-20b model (see console.groq.com/docs/content-moderation
# for the required INSTRUCTIONS/DEFINITIONS/VIOLATES/SAFE/EXAMPLES format).
MODERATION_POLICY = """# Hospital Data Assistant — Output Safety Policy

## INSTRUCTIONS
Classify whether the given AI-generated answer about hospital/healthcare data
contains harmful content. Return a JSON object with your decision and
reasoning.

## DEFINITIONS
- Harmful content: hate speech or slurs targeting a group, sexual content,
  instructions enabling violence or weapons, encouragement of self-harm, or
  identifiable private medical/personal information about a specific real
  individual patient (not public facility data like hospital names,
  addresses, or aggregate ratings, which are expected and fine).

## VIOLATES (1)
- Hateful or discriminatory language targeting a group
- Sexual content
- Instructions that enable violence, weapons, or harm to people
- Content encouraging self-harm or suicide
- Specific, identifiable personal/medical details about a real patient

## SAFE (0)
- Factual information about hospitals, ratings, infections, physicians, or
  CMS methodology
- Public facility names, addresses, phone numbers, or aggregate statistics
- Polite refusals or clarifying questions

## EXAMPLES
Example 1 (Violation):
Content: "Here is how you can make a pipe bomb at home: step 1, gather..."
Answer: {"violation": 1, "category": "Violence/Weapons", "rationale": "Provides instructions enabling physical harm."}

Example 2 (Safe):
Content: "São Paulo tem 42 hospitais avaliados, com média de 3.8 estrelas."
Answer: {"violation": 0, "category": null, "rationale": "Factual public hospital statistics."}

Content to classify: {{CONTENT}}
Answer (JSON only):"""


def redact_pii(text: str) -> tuple[str, list[str]]:
    categories = []
    redacted = text or ""
    for name, pattern in PII_PATTERNS:
        if pattern.search(redacted):
            categories.append(name)
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted, categories


async def check_harmful_content(text: str) -> dict:
    if not text or not text.strip():
        return {"flagged": False, "categories": []}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": SAFETY_MODEL,
                    "messages": [
                        {"role": "system", "content": MODERATION_POLICY},
                        {"role": "user", "content": text},
                    ],
                },
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        verdict = json.loads(content)
    except Exception as e:
        logger.error("safety_model_check_failed", error=str(e))
        return {"flagged": False, "categories": []}

    if not verdict.get("violation"):
        return {"flagged": False, "categories": []}

    category = verdict.get("category")
    return {"flagged": True, "categories": [category] if category else []}


async def moderate_content(text: str) -> dict:
    """Run both moderation layers against a final answer's explanation text.

    Returns:
        {
            "text": <redacted text — use this as the actual answer>,
            "pii_categories": [...],      # e.g. ["email", "phone"]
            "harmful_flagged": bool,       # safety-model verdict
            "harmful_categories": [...],  # e.g. ["Violence/Weapons"], if flagged
        }
    """
    redacted_text, pii_categories = redact_pii(text)
    harmful = await check_harmful_content(redacted_text)
    return {
        "text": redacted_text,
        "pii_categories": pii_categories,
        "harmful_flagged": harmful["flagged"],
        "harmful_categories": harmful["categories"],
    }