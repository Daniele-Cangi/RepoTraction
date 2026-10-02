"""Narrow descriptive-gap hints; never infer permission from absent constraints."""
import re

# Mixed observation/instruction stays a potential constraint. This deliberately
# errs toward review instead of interpreting every negative English sentence.
_DIRECTIVE = re.compile(
    r"\b(?:must|shall|should|never|cannot|requires?|required|ensure|expected|keep|leave|preserve|maintain|"
    r"forbidden|prohibited?|without|avoid|exclude)\b|\bmake\s+sure\b|"
    r"\b(?:may|do|can)\s+not\b|\b(?:don't|can't|mustn't|shouldn't)\b|"
    r"\bno\s+(?!built-in\b)|\bzero[- ]dependenc(?:y|ies)\b", re.I)
_ABSENT_BUILTIN = re.compile(r"\bthere\s+(?:is|are)\s+(?:currently\s+)?no\s+built-in\b", re.I)
_EXISTING_SANITIZER = re.compile(
    r"\b(?:current\s+(?:implementation|parser|logger|code)|existing\s+(?:implementation|parser|logger|code)|"
    r"logging\s+path|shared\s+sink|companion\s+script)\b[^.;:\n]{0,100}\bdoes\s+not\s+"
    r"(?:strip|sanitize|neutralize)\b", re.I)


def current_gap_hint(sentence):
    """Only source-observation grammar; ambiguity and any directive keep review."""
    return bool(not _DIRECTIVE.search(sentence) and len(re.findall(r"\bdoes\s+not\b", sentence, re.I)) <= 1
                and (_ABSENT_BUILTIN.search(sentence) or _EXISTING_SANITIZER.search(sentence)))
