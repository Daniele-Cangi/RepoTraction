# Acceptance notes before autonomous source selection

No model run, repository candidate search or donor inspection has occurred for
this cohort. These are assessor notes, not model inputs or adjudicated outcomes.
The protocol was written before the one-result issue search; the query returned
WilliamNT/tunesynctool #21. We retain it even though its discussion may justify
waiting for protocol support rather than importing a new package.

## Historical control: audio-feeder #81

Reuse the frozen #122 acceptance: case/diacritic-insensitive author sorting,
original string tie-break, unchanged displayed names and native target behavior.
Its known direct standard-library correction passed 128/128 acceptance assertions
across the preserved HTTP cases, versus 112/128 for the original target. These
are historical measurements, not outcomes of the new run. Check live discussion
and revision drift when interpreting the result. An unnecessary new package is
not advantageous just because it can normalize strings. Correct abstention is
progress over the lexical choices, but not a new useful reuse.

## Fresh primary: tunesynctool #21

Request: https://github.com/WilliamNT/tunesynctool/issues/21 . Read the issue and
all four available comments before looking at any donors. The owner has already
added mapping of returned ISRC values; the remaining request is retrieval by ISRC.
The June 7 owner comment requires specification consistency and maintainability,
and accepts investigating a best-effort query with harmless empty results. The
requester also considers waiting for specific API support reasonable. Therefore
universal cross-server retrieval is **not established as currently implementable**.

Pinned target: `b705691ba7d02d34ff3b6423ca03fcfca1514994`.
Read its manifest and `tunesynctool/drivers/common/subsonic/{driver,async_driver,mapper}.py`.
The manifest already depends on `py-sonic`; the driver uses its `Connection`.
`get_track_by_isrc` raises `NotImplementedError`; `search_tracks` uses `search2`;
the mapper retains the first supplied ISRC; the asynchronous driver wraps the
synchronous implementation. These are static observations, not executed behavior.

Acceptance, independent of a future donor:

1. For a server that returns appropriately ISRC-tagged matching tracks, expose
   exact recording lookup through the target's existing driver interface, without
   MusicBrainz traffic. A lexical title match is not an exact ISRC match.
2. Preserve source service identity and existing mapped track data. Distinguish
   missing tags, no results, multiple results and unsupported search from proof
   of a universally absent recording. The issue does not specify tie-breaking;
   leave that policy unknown until justified against the existing interface.
3. Keep existing driver behavior, asynchronous wrapping and playlist/mapping
   tests working. No claim of server portability based only on a fake response.
4. Respect the owner's specification/maintenance constraint. A custom Gonic-only
   convenience or an undocumented query is not proof of general support.

Strongest direct alternative to examine first: extend the existing py-sonic
connection path with the discussion's proposed `search3` ISRC query, validate
returned identifiers exactly, and use the target's existing miss/error behavior.
No new package is inherently needed for string equality or DTO mapping. This
alternative is **unexecuted and conditional on actual server/client support**;
do not certify adequacy from the discussion or supplied four-file sample alone.
Waiting with a precise explanation is also admissible where protocol support is
the blocker. Reimplementing MusicBrainz lookup would violate the intended benefit.

A donor can improve on this only by supplying an already implemented missing
operation with a concrete advantage, such as demonstrably supported portable
lookup that the direct path lacks, or less total integration/maintenance work.
Existing dependencies and already named projects count as prior context, not an
unexpected discovery. The model may choose other operations if grounded in the
request; assess them against these criteria rather than our favored mechanism.

If a source is selected, compare original target, strongest direct implementation
and reuse integration on the same target revision and native tests. Record network
calls, exact/missing/misleading/multiple tag cases, adapter logic, new dependencies
and backend coverage. Use a real conforming server with controlled tagged media
for any portable retrieval claim; a mocked client proves only client integration.
If server access or semantic guarantees are unavailable, report that limit and
do not claim useful end-to-end reuse. No third-party publication or user account
access is part of this experiment.

This small cohort can expose poor decisions and possibly show one useful lead;
two correct stops would demonstrate restraint, not autonomous useful discovery.
