# Luna branch comparison result and remaining limits

The frozen nine-case comparison completed with `gpt-6-luna`. **The result is
mixed, not a production acceptance:** command-generation versus boolean matching
is now distinguished, and two overstated `want_bytes` return claims disappear.
The mean slice and resolver-versus-search-factory contrasts survive. A useful
timestamp mechanism contrast is lost, and an abstention explanation misidentifies
a factory as its returned wrapper. There is still no qualified lead.

## Execution and accounting

PR69 merged as `6b655c7` after a no-findings Codex review of `291fe24` and four
successful CI jobs. Execution followed the
[frozen protocol](missing-link-triage-branch-execution-protocol-2026-10-05.md):
nine original contexts, unchanged model/options/schema/normalization, fresh CLI
identity checks, one request per case and no retries. No previous prediction or
reviewer label was sent. No acquired repository code ran.

All nine native terminal events are completed; full decoded envelopes are retained
privately. Their message text equals the separately saved parsed cards. Request
hashes/bytes match the manifest, and native token usage matches the job receipts.
All nine cards replay identically through normalization with no validation error.
These checks establish transport and provenance, not semantic accuracy.

| Accounting item | Observed value |
| --- | ---: |
| New requests and reservations | 9 |
| New conservative reservations USD | 0.0702980 |
| Segment cap USD | 0.1000000 |
| Original allowance reservations | 507 |
| Original allowance reserved USD | 7.5430970 |
| Segment cumulative ceiling USD | 7.5727990 |
| Original cumulative cap USD | 10.0000000 |
| Native input tokens | 113,209 |
| Native output tokens | 15,944 |
| Usage estimate at configured prices USD | 0.0192929 |
| Combined triage reservations USD | 0.3307904 |

The configured standard rates are USD0.10 input / USD0.50 output per million
tokens, consistent with the [Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna).
The usage estimate is not an invoice and does not replace reservations. Earlier
failed attempts retain unknown native usage and remain charged conservatively.
No allowance reset, refund or second execution occurred.

All 498 prior reservation rows, other allowances, ten non-accounting table hashes
and 580 historical artifact hashes remain unchanged. Only the original allowance
increment and nine exact owned reservation rows differ. Existing jobs are not
resumed or imported, and no ranking, qualification or production flag changes.

## Independent reading of the responses

Seven facets now have a non-unknown relation, versus eight previously; there are
29 abstentions, versus 28. This is an observation, not a score. Independent source
reading supports the seven local claims with the limits below. Removed claims are
not all losses: two were previously overgeneralized. No automatic gold labels or
model self-certification are introduced.

| Case | Observed comparison and independent assessment |
| --- | --- |
| 1 Copy publication | All unknown, appropriately leaving atomicity of the unseen copy delegate open. However, input/output explanations describe `src`/`dst` and the copy-result return as the selected entrypoint. `only_newer(copy_func)` is actually the factory returning `wrapper`; those properties belong to the wrapper. This is an explanation defect even without a certified relation. |
| 2 Grep generation | Output and outcome change from unknown to different. The acceptance chunk requires command text with grep options; the selected body returns `fnmatchcase` matching of a filename. Both local contrasts are supported without claiming adoption, a runtime ban or whole-task rejection. |
| 3 POSIX traversal | All unknown. Broad conformance requirements, incomplete acquisition and the unseen `follow` callback do not establish the exact requested behavior. Generic traversal is not automatically a verified find slice. |
| 4 Mixed input conversion | The declared primary `str`/`bytes` input contrast survives. It is not runtime collection rejection or exact arity: optional encoding/errors parameters also exist. Output and outcome become unknown; the explanation now recognizes string encoding and non-string pass-through instead of asserting every return is bytes. Passing through a collection still does not establish mixed-dtype detection. |
| 5 Research codec | All unknown. Serialization, optional compression and encoding do not establish the complete reversible-codec study, measurement or unseen decoding helpers. A possible primitive is not a qualified match. |
| 6 External anchoring | Outcome becomes unknown. No external-anchor slice is invented, but a previously supported narrow contrast is omitted: the cited request requires `ots stamp` and a public proof, while the visible method concatenates value, encoded timestamp and signature results. Unseen helpers remain unknown; this does not justify full-workflow rejection. |
| 7 Key grouping | All unknown. The selected function delegates to unseen `nest`; exact grouping behavior and return shape remain unestablished. JavaScript syntax does not establish a runtime incompatibility. |
| 8 Hosted URI resolver | Input/output/outcome remain different. The cited version/topic-to-URI interface contrasts with the selected comparator/accessor factory returning search methods. The comparison correctly stays at the factory layer, not its methods' numeric results or whole-product compatibility. |
| 9 Profiling average | Outcome remains slice. The cited request explicitly includes `avg`; the selected body computes sum/count over qualifying values. Other statistics, numeric/coercion policy, infinities, errors and adoption remain open. This is a bounded useful primitive, not complete profiling or an eligible lead. |

All nine runtime facets remain unknown. All demand-complete flags are false; every
card remains `context_required`. Neither semantic-verification flag is set and
qualification/selection remain unchanged. Unknown is not counted as a correct
rejection. A source-grounded negative contrast is not automatically a rejected
production candidate; the mean slice is not automatically an isolated connection.

## Preservation and next decision

The old responses, including their overstated claims, remain intact. New full
terminal receipts, parsed cards, mechanical audit and independent reading are kept
separately under `data/missing-link-triage-branch-execution-2026-10-05/` and are not
published as raw text or imported into the UI. SHA256 of the private artifacts:

| Artifact | SHA256 |
| --- | --- |
| results.json | `02fc4a14adb936c08e482d9aac41b77aabf6fe9c34baadec58262b6db47aac95` |
| audit-summary.json | `8cad51a7baae56e08ac35329b464e1075e3168b2267d74194bf3df4cdf2e0c45` |
| semantic-review.json | `6f7afb01d9aa8136d598953033e0fa2ababe4027569d870ad9e77b210599d46c` |
| final-integrity.json | `143b61fa1672659f23f20b55805aa25a94dde70331dbc8f60cc7ecee6e9a559b` |

The post-run 206 focused tests, 1,186 full-suite tests and CLI help pass. A separate
post-test preservation check reproduces nine unchanged cards, historical artifacts,
accounting and completed receipts without another model call.

Do not promote this prompt, force a positive lead or repeat these nine paid cases
automatically. Next, establish no-spend paired source-reading controls for factory
versus returned-wrapper explanations and visible mechanism contrasts with unseen
delegates. Keep full external anchoring unknown. This is not a request for broader
parser coverage or a universal semantic classifier. Any later autonomous usefulness
test needs its own frozen protocol; this retrospective run is not held-out accuracy.
