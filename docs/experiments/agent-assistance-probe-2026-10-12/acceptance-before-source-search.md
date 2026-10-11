# Independent native acceptance for pytest #15099

The revised pool's first result is selected: pytest #15099, at target
`587ebc501ba292539202a1aac3a7f5b0112a08ec`. Its complete six-comment discussion
still has no merged resolution. PR #15118 is open, head
`68cb1befd6baf84432b046fe9d703315e5f7221d`; the later duplicate #15130 was closed.
The existing proposal is part of the strongest available direct baseline, not an
unknown donor. It is disclosed to all agents through the complete discussion.
The root report itself suggests a fix; do not hide that suggestion to weaken the
control. No Missing Link source/candidate has been searched.

## Acceptance, fixed before agents or donors

1. Run the public two-test reproduction in actual pinned pytest. Teardown must
   not raise `AttributeError`; the following test must observe the original
   value, not the patch leaked from the preceding test.
2. Restore custom storage through its established object interface. Inherited
   hooks and repeated/nested patches must preserve the original value.
3. Preserve the current native restoration semantics: undo must remove a newly
   created instance shadow of an inherited attribute, so subsequent class changes
   and non-data descriptor resolution remain visible. Existing instance values
   must be restored by identity. Data descriptors and slots still work.
4. Run `testing/test_monkeypatch.py` and the relevant target-native fixture tests,
   with the original target suite unchanged. A fix cannot pass by removing tests,
   changing the reproduction, editing third-party source, permanently changing
   example objects, adding a special case for a fixture's name or skipping cases.

The assessor's eight additional cases apply those existing semantics to proxy,
inherited-hook, passthrough-hook and mixed-storage examples. The passthrough/mixed
cases are inferred generalizations of native #10644 tests, not additional explicit
acceptance stated by the issue author. Disclose this distinction. They are prepared
before donor search; they must not be altered after seeing a candidate or patch.
Their concrete data is withheld from development prompts, while the semantic
requirements above remain public. Report public reproduction, native regression
suite and assessor generalizations separately; an assessor-only failure is not
proof that an upstream maintainer rejects the patch.

## Comparator and limits of claims

Evaluate the current pinned code, the existing direct PR proposal, the common
unaided attempt and both continuation patches on the same frozen tests. Native
results and residual failures decide useful assistance; count changed mechanisms,
not extra matched words or libraries. Measure target logic/dependencies and observed
time as well. A successful continuation must be source-traceable and improve on
the ordinary continuation, or demonstrate a bounded concrete improvement over the
common failed attempt that the ordinary continuation misses.

An ordinary continuation can inspect the supplied upstream proposal and investigate
other sources. If that already solves everything, report that result. If the
common attempt already meets all criteria, there is no blocked agent to help and
the source/continuation comparison stops. No target-wide correctness, economic
gain, maintainer acceptance or new general capability follows from this one case.
No patch is submitted to pytest or merged automatically.
