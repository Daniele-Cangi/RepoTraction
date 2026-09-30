"""Human-reviewed fixtures derived from the requested word-boundary outcome.

Run ONLY in the opt-in WASI example API with the pinned generated example and
public source. Inputs/budgets below are assumptions, not original issue fixtures.
Passing ordinary fixtures does not establish production integration. The long
first-word case deliberately detects the source helper's hard-slice fallback.
"""
import json

try:
    from example import truncate_meta_description  # initial generated proposal
except ModuleNotFoundError as error:
    if error.name != "example":
        raise
    from examples.meta_description import truncate_meta_description  # refined API proposal

CASES = [
    ("ordinary_words", "red fox jumps", 10, "red fox"),
    ("prose_is_not_a_slug", "A Quick, brown fox jumps", 16, "A Quick, brown"),
    ("preserve_prefix_order", "alpha encyclopedia cat", 12, "alpha"),
    ("oversized_first_word_policy_missing", "encyclopedia next", 5, ""),
]

results = []
for label, text, budget, expected in CASES:
    actual = truncate_meta_description(text, budget)
    results.append({"fixture": label, "input": text, "assumed_budget": budget,
        "expected_under_strict_no_partial_words_policy": expected,
        "actual": actual, "ordinary_slice_baseline": text[:budget], "passed": actual == expected})
print(json.dumps({"context": "controlled_fixtures_not_target_integration", "results": results,
    "strict_no_partial_words_policy_is_an_assumption": True,
    "original_request_does_not_define_oversized_word_behavior": True}, indent=2))
assert all(result["passed"] for result in results), "Original helper has an oversized-first-word fallback; choose and implement an explicit policy before claiming strict whole-word compliance."
