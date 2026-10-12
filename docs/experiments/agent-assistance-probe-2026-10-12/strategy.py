"""Experiment-only goal/context injection into the existing discovery path.

No transport, dispatch loop or product mode. The normal Service, contracts, budget,
source inspection and handoff remain responsible for execution and validation.
"""
import copy
import json
from pathlib import Path

from missing_link.discovery_decisions import (
    plan_input, plan_schema, resolve_plan, resolve_selection, selection_schema,
)
from missing_link.provider import CandidateValidationError, Provider
from missing_link.analysis import digest
from missing_link.proofs import _evidence, export_handoff
from missing_link.service import Service
from missing_link.sources import _redact

PROMPTS = json.loads(Path(__file__).with_name("prompts.json").read_text(encoding="utf-8"))
TARGET_REVISION = "587ebc501ba292539202a1aac3a7f5b0112a08ec"
FROZEN_INPUT_FINGERPRINT = "9b45c38282d1ab028e6cd0ac4609f483dcb81658898866e6ca718f8fbd75470d"


class FrozenAssistanceService(Service):
    """Reuse Service execution with two explicitly frozen experiment inputs."""
    def __init__(self, *args, frozen_inputs, **kwargs):
        frozen = copy.deepcopy(frozen_inputs)
        issue, target = frozen["issue"], frozen["target"]
        if (digest(frozen) != FROZEN_INPUT_FINGERPRINT or target["revision"] != TARGET_REVISION
                or target["full_name"] != "pytest-dev/pytest" or target.get("public") is not True
                or issue.get("public") is not True or issue["repo_id"] != target["id"]
                or issue["url"] != "https://github.com/pytest-dev/pytest/issues/15099"):
            raise ValueError("Frozen demand/target identity or content changed.")
        self.frozen_inputs = frozen
        super().__init__(*args, **kwargs)

    def _prepare_request_discovery(self, job, source, budget, stage, save):
        frozen = self.frozen_inputs

        class FrozenReads:
            def fetch_issue(self, url):
                if url != frozen["issue"]["url"]:
                    raise ValueError("This cohort contains one frozen demand only.")
                return copy.deepcopy(frozen["issue"])

            def fetch_reference_context(self, issue, *, include_catalog=False):
                if issue["fingerprint"] != frozen["issue"]["fingerprint"]:
                    raise ValueError("Frozen discussion changed before target inspection.")
                return copy.deepcopy(frozen["target"])

            def __getattr__(self, name):
                # Inquiry still uses the normal explicit pinned-revision read;
                # source search/inspection keep normal budgets and account checks.
                return getattr(source, name)

        budget.checkpoint()
        return super()._prepare_request_discovery(job, FrozenReads(), budget, stage, save)


def assistance_packet(match, repository):
    """Deterministic, lossless-or-stop projection of the existing handoff."""
    handoff = export_handoff(match, repository)
    if repository.get("public") is not True or repository.get("id") != match.get("repo_id"):
        raise ValueError("Packet needs the acquired public source identity.")
    files = {f["path"]: f for f in repository["files"]}
    snippets, omitted_evidence, seen = [], [], set()
    for index, evidence in enumerate(_evidence(handoff)):
        path = evidence.get("path")
        if path not in files:
            omitted_evidence.append({"index": index, "reason": "Not a retained source-file reference."})
            continue
        start, end = evidence.get("line"), evidence.get("end_line", evidence.get("line"))
        lines = files[path]["text"].splitlines()
        if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines)):
            raise ValueError("Cited source span is outside frozen evidence; no clipping.")
        key = (path, start, end)
        if key in seen:
            omitted_evidence.append({"index": index, "reason": "Duplicate retained source span."})
            continue
        seen.add(key)
        snippets.append({"path": path, "sha": files[path]["sha"], "line": start, "end_line": end,
                         "url": files[path]["url"].split("#")[0] + f"#L{start}-L{end}",
                         "text": "\n".join(lines[start - 1:end])})
    if not snippets:
        raise ValueError("No retained cited source excerpt; stop this cohort.")
    selected = {key: handoff["match"].get(key) for key in
                ("id", "capability_id", "capability", "classification", "summary", "limitations")}
    bridge = handoff["bridge"]
    retained_bridge = ("existing_contribution", "assumptions", "limitations")
    packet = {"purpose": "Unverified source mechanism for agent investigation; no target bridge code.",
        "repository_id": repository["id"], "repository": handoff["repository"],
        "revision": handoff["revision"], "match": selected, "source_excerpts": snippets,
        "contribution": {key: bridge.get(key) for key in retained_bridge},
        "verification": handoff["verification"], "warnings": handoff["warnings"],
        "omitted_fields": sorted([key for key in handoff if key not in
            {"repository", "revision", "match", "verification", "warnings", "bridge"}]
            + ["match." + key for key in handoff["match"] if key not in selected]
            + ["bridge." + key for key in bridge if key not in retained_bridge]),
        "omitted_evidence": omitted_evidence}
    payload = (json.dumps(packet, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    clean, redacted, truncated = _redact(payload.decode("utf-8"))
    if len(payload) > 16000 or clean.encode("utf-8") != payload or redacted or truncated:
        raise ValueError("Packet exceeds 16000 bytes or needs redaction; stop, do not trim.")
    return payload


class AssistanceProvider(Provider):
    def __init__(self, env, agent_attempt):
        super().__init__(env)
        keys = {"approach", "observed_failure", "verification"}
        if not isinstance(agent_attempt, dict) or set(agent_attempt) != keys:
            raise ValueError("Provide a recorded approach, failure and verification.")
        for value in agent_attempt.values():
            if not isinstance(value, str) or not value.strip() or len(value) > 4000:
                raise ValueError("Recorded agent context exceeds its explicit bound.")
            clean, redacted, truncated = _redact(value)
            if clean != value or redacted or truncated:
                raise ValueError("Recorded agent context needs redaction or truncation.")
        self.agent_attempt = copy.deepcopy(agent_attempt)

    def plan_discovery(self, request, target, budget, *, inquiry=None):
        data = plan_input(request, target, inquiry)
        data["agent_attempt"] = self.agent_attempt
        data["experimental_goal"] = "assist_development_agent"
        raw = self.complete(PROMPTS["plan"], data, budget, plan_schema(request), "request")
        try:
            result = resolve_plan(raw, request, self.identity())
        except (ValueError, TypeError, KeyError):
            raise CandidateValidationError("Invalid experimental assistance decision; no retry.") from None
        result["target_snapshot"] = {key: value for key, value in data["target"].items() if key != "files"}
        result["target_snapshot"]["files"] = [{key: value for key, value in f.items() if key != "text"}
                                               for f in data["target"]["files"]]
        result["context_coverage"] = data["context_coverage"]
        result["experimental_goal"] = "assist_development_agent"
        result["agent_attempt"] = copy.deepcopy(self.agent_attempt)
        return result

    def select_source(self, plan, candidates, budget):
        data = {"plan": plan, "candidates": candidates,
                "context_coverage": {"decision_version": plan["version"],
                                     "repository_metadata_only": True, "source_code_available": False}}
        raw = self.complete(PROMPTS["selection"], data, budget, selection_schema(plan, candidates), "request")
        try:
            result = resolve_selection(raw, plan, candidates)
        except (ValueError, TypeError, KeyError):
            raise CandidateValidationError("Invalid experimental source selection; no retry.") from None
        result["experimental_goal"] = "assist_development_agent"
        return result
