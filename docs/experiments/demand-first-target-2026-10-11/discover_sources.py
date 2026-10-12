"""One frozen, unpaid source-selection experiment; no execution or AI transport."""
import itertools
import json
import re
import sys
from pathlib import Path


STOP = set("a an the we i should would be been being using use uses used for these those this that things out and or to of with in by on is are going purposes version non".split())


def queries(protocol):
    # Source-independent normative sentence, retained verbatim from the issue.
    words = re.findall(r"[a-z]+", protocol["normative_sentence"].lower())
    chunks = [list(group) for keep, group in itertools.groupby(words, lambda w: w not in STOP) if keep]
    phrases = []
    for chunk in chunks:
        if len(chunk) < 2 and len(chunk[0]) < 8:
            continue
        chunk = [word[:-1] if len(word) >= 5 and word.endswith("s") and not word.endswith("ss") else word for word in chunk]
        phrase = " ".join(chunk[:3])
        if phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) == 3:
            break
    return [phrase + " language:Python archived:false fork:false in:name,description,readme" for phrase in phrases]


def select(protocol, batches):
    expected = queries(protocol)
    if [batch["query"] for batch in batches] != expected:
        raise ValueError("Search results must match the frozen query order.")
    selected, seen = [], {protocol["target_repository"].casefold()}
    # GitHub's returned rank, round-robin across the three need phrases. No
    # package allowlist, manually substituted source or score adjustment.
    for rank in range(20):
        for query_index, batch in enumerate(batches):
            if rank >= len(batch["items"]):
                continue
            item = batch["items"][rank]
            name = item["full_name"]
            if name.casefold() in seen:
                continue
            if item.get("private") or item.get("fork") or item.get("archived"):
                continue
            if item.get("language") not in (None, "Python"):
                continue
            seen.add(name.casefold())
            selected.append({"repository": name, "query_index": query_index,
                             "upstream_rank": rank + 1, "qualification": "unassessed"})
            if len(selected) == 3:
                return selected
    return selected


if __name__ == "__main__":
    protocol = json.loads(Path(__file__).with_name("protocol.json").read_text(encoding="utf-8"))
    result = queries(protocol) if len(sys.argv) == 1 else select(protocol, json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["batches"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
