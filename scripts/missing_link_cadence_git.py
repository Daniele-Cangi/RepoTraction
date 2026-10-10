"""Exact Git identity and worktree gate; no subprocess or other IO on import."""
from dataclasses import dataclass
import re

from scripts.missing_link_repository_only_evaluator import require
from scripts.missing_link_repository_only_run import git


@dataclass(frozen=True)
class GitTreeAudit:
    """One immutable commit/tree binding, freshly checked on every invocation."""
    head: str
    tree: str
    run: object = git

    def __post_init__(self):
        require(all(type(value) is str and re.fullmatch(r'[a-f0-9]{40}', value)
                    for value in (self.head, self.tree)) and callable(self.run),
                'Invalid Git audit binding')

    def __call__(self):
        # Resolve both names in the same process; keep the explicit tree check
        # and a separate fresh porcelain status check before accepting the gate.
        require(self.run('rev-parse', 'HEAD', 'HEAD^{tree}').splitlines() == [self.head, self.tree],
                'Measured implementation identity changed')
        require(not self.run('status', '--porcelain'), 'Measured worktree changed')
