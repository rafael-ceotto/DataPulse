#Post-hoc ground check for AI agent's final answer -> double check to avoid hallucination

import re

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")

# 1 -> Numbers too small/common to be worth flagging e.g. star ratings, list positions, round %, etc. 
# -> which would trigger on almost every answer

IGNORE_NUMBERS = {"0", "1", "2", "3", "4", "5", "10", "100"}

def looks_like_year(value: float) -> bool:
    return value == int(value) and 1900 <= value <= 2099

def extract_numbers(text: str) -> set[str]:
    #Tokenizer out of text
    #Calendar years(1900-2099) are dropped -> show up in prose
    numbers = set()
    for match in NUMBER_RE.findall(text or ""):
        cleaned =  match.replace(",", "")
        try:
            value = float(cleaned)
        except ValueError:
            continue
        if looks_like_year(value):
            continue
        normalized = str(int(value)) if value == int(value) else str(value)
        numbers.add(normalized)
    return numbers

def check_grounding(explanation: str, tool_outputs: list[str]) -> dict:
    #Check whether numeric fig cited in explanation appear somewhere else, specially in raw 'tool_outputs'
    #Returns {'checked': True, 'unverified_numbers': [...]} _ if empty list, then every citer number was found somewhere else
    cited = extract_numbers(explanation) - IGNORE_NUMBERS
    if not cited: 
        return {"checked": True, "unverified_numbers": []}
    
    available: set[str] = set()
    for output in tool_outputs:
        available |= extract_numbers(output)
    
    unverified = sorted(cited - available, key=lambda n: -len(n))
    return {"checked": True, "unverified_numbers": unverified}
