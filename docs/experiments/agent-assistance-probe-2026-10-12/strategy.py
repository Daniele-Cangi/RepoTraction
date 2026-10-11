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
from missing_link.sources import _redact

PROMPTS = json.loads(Path(__file__).with_name("prompts.json").read_text(encoding="utf-8"))


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
