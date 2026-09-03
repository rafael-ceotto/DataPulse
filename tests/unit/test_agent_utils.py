from app.ai.hospital_agent_service import clean_content

def test_clean_content_removes_think_tags():
    content = "<think>This is internal reasoning</think>Final answer here"
    result = clean_content(content)
    assert result == "Final answer here"


def test_clean_content_removes_unclosed_think_tag():
    content = "Some text <think>This reasoning never closes"
    result = clean_content(content)
    assert result == "Some text"


def test_clean_content_removes_tool_call_tags():
    content = "<tool_call>search_hospitals</tool_call>Here is the result"
    result = clean_content(content)
    assert result == "Here is the result"


def test_clean_content_removes_function_tags():
    content = "<function name='search'>args</function>Clean response"
    result = clean_content(content)
    assert result == "Clean response"


def test_clean_content_empty_string():
    result = clean_content("")
    assert result == ""


def test_clean_content_no_tags():
    content = "This is a clean response with no tags"
    result = clean_content(content)
    assert result == content


def test_clean_content_strips_whitespace():
    content = "  <think>thinking</think>  Final answer  "
    result = clean_content(content)
    assert result == "Final answer"