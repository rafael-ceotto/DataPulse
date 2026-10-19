import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.grounding_check import check_grounding

OH_VT_TOOL_OUTPUTS = [
    '{"OH": {"avg_rating": 3.1}, "VT": {"avg_rating": 3.6}}',
    '{"state": "OH", "total_measures": 170892, "worse_than_national": 2820, "better_than_national": 31255}',
    '{"state": "VT", "total_measures": 13865, "worse_than_national": 282, "better_than_national": 564}',
    '{"results": ["[Source: CMS Methodology Report v3.0, Page 12, Similarity: 0.91]\\nStar ratings are calculated using..."]}',
]

CASES = [
   (
        "All cited numbers present in tool data (Ohio/Vermont style answer)",
        "Ohio reported 170,892 measures total, with 2,820 worse than the national benchmark "
        "and 31,255 better. Vermont reported 13,865 measures, with 282 worse and 564 better.",
        OH_VT_TOOL_OUTPUTS,
        [],  # expected unverified_numbers
    ),
    (
        "Fabricated number not present anywhere in tool data",
        "Ohio reported 999999 measures total, far more than any tool call returned.",
        OH_VT_TOOL_OUTPUTS,
        ["999999"],
    ),
    (
        "No numbers cited at all — nothing to check",
        "Ohio performed worse than Vermont on infection measures overall.",
        OH_VT_TOOL_OUTPUTS,
        [],
    ),
    (
        "Small/common numbers (ratings, list positions) are ignored, not flagged",
        "Ohio has a 3-star rating and Vermont has a 4-star rating; both are in the top 5.",
        OH_VT_TOOL_OUTPUTS,
        [],
    ),
    (
        "Thousands-separator formatting still matches the raw tool number",
        "Ohio had 170,892 total measures.",
        OH_VT_TOOL_OUTPUTS,
        [],
    ),
    (
        "No tool outputs at all (e.g. a web_search-only question) — any real number is unverified",
        "Hospital staffing shortages affected 12345 facilities in 2026.",
        [],
        ["12345"],
    ), 
]

def main():
    failures = []
    for description, explanation, tool_outputs, expected_unverified in CASES:
        print(f"\n=== {description} ===")
        result = check_grounding(explanation, tool_outputs)
        print(f"  unverified_numbers={result['unverified_numbers']}")

        if sorted(result["unverified_numbers"]) != sorted(expected_unverified):
            failures.append((
                description,
                f"expected unverified_numbers={expected_unverified}, got {result['unverified_numbers']}",
            ))

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED: {len(failures)} issue(s)")
        for desc, msg in failures:
            print(f"  - [{desc}] {msg}")
        sys.exit(1)
    else:
        print(f"PASSED: all {len(CASES)} cases behaved as expected.")


if __name__ == "__main__":
    main()