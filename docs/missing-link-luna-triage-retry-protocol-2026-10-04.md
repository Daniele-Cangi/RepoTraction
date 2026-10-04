# Corrected Luna triage test protocol

This fresh retrospective test evaluates demand-to-mechanism extraction on the
same nine retained public source/discussion pairs. The user authorized fixing
the harness and proceeding on 2026-10-04. The [stopped first attempt](missing-link-luna-triage-result-2026-10-04.md)
remains failed, with unknown native usage; it is neither refunded nor resumed.
This protocol is committed and pushed before any new paid request.

## Harness corrections

`scripts/missing_link_triage_transport.py` is experimental and not imported by
production discovery. Its identity adapter requires a fresh fixed-account check
before every actual request, reuses only successful checks for less than three
seconds during streaming, and invalidates success before another check. Failed
checks propagate. Cancellation and allowance checks still run through the
existing `Budget`; production provider code and its 240-second deadline are unchanged.

The wire schema uses strings for all evidence references. Unknown references
must be empty strings, mapped to `None` only in a copied response before the
existing offline span checker. Raw output is preserved. Known relations, quotes
and evidence IDs are not repaired. The prompt changes only the declared unknown
sentinel from null to empty strings. Nullable unions are supported by the
[OpenAI API](https://developers.openai.com/api/docs/guides/structured-outputs),
but not by this application's intentionally narrower local validator.

Seven public adapter regressions include a real `Provider.complete` call with
an injected 150-frame stream, strict schema validation, usage and output receipts.
Six private harness fixtures verify the frozen input round trip, unknown mapping,
missing acquisition, forged quotes and original operation spans. They perform
no paid calls or network requests. They demonstrate the corrected paths, not
the exclusive cause of the earlier live timeout.

## Frozen inputs and spending

Inputs are byte-equivalent after JSON serialization to the earlier frozen nine
cases. No fresh GitHub acquisition, reference labels, prior AI verdicts or human
annotations are sent. The source revisions, selected operations and discussion
fingerprints remain pinned by the [original protocol](missing-link-luna-triage-protocol-2026-10-04.md).
This is a retrospective comparison, not held-out accuracy or autonomous discovery.

Use `gpt-6-luna`, Responses, strict structured output, streaming, medium reasoning,
6,000 maximum output tokens and the existing configured prices. One request per
case, at most nine requests, no automatic retries. Do not edit `.env`, import an
analysis into jobs, execute acquired code, or resume other investigations.

The original allowance starts at 462 reservations / USD7.2165095. The earlier
USD0.0042029 reservation counts toward the combined USD0.20 test cap. Therefore
the atomic reservation ceiling is USD7.4123066, not baseline plus another USD0.20.
The remaining incremental cap is USD0.1957971; all nine prepared requests require
USD0.0552100. Including the failure, the maximum prepared reservation is
USD0.0594129. Reservations are upper bounds, not invoices or reported token usage.
The original USD10 cumulative allowance remains unchanged.

## Request fingerprints

Private driver SHA256: `45c0b378e9efab747040006e38f5576d364cca72cfbbaf61788a58bc7d79562a`.
Public adapter SHA256: `241a2a6ae5109c2517c70a869a82efb7db2c5daeaca738bd6b20c375ce2be982`.
Prompt SHA256: `50b8c0ad2d2579ef9c3a56d155e87cb95f9c0dcfaa2763bcfb90868f2bd51315`.
Schema SHA256: `15f84d92aea2da685f5104bc9f4710e97b0148fc343a0aad650ec4a79615f1e3`.

| Case | Serialized bytes | Request SHA256 |
| --- | ---: | --- |
| 1 | 9870 | `a48d456556a70570f581ac6b4510b71de14fca3b6c069040dfed1b8dedfadbf5` |
| 2 | 11712 | `7cdcdd1c9a00f5ea7dc0bb3a4ddfefaf5578fbfbaa9a26baff6ffe749d4fc5ba` |
| 3 | 107599 | `93cd3f879ccf4e3167b50bb64af02ff95179a0faa4256851e883ad413784f445` |
| 4 | 7105 | `e1fb1fa96915fb7d5a0858618403a58689c2af987a1169746d576be482223071` |
| 5 | 28676 | `70bdc42f7939f37c505b165f565152e7bdfb63bfaafc669c571088f5ad42f209` |
| 6 | 8619 | `a03984e51daec158a53300014c022e1ba68a7aa2a863fdde9e6cf2a4dc433044` |
| 7 | 9331 | `7b75f26c0cc6659a89605de36bc3e9c02358f576b7e7bdf094f95daa58231f25` |
| 8 | 65608 | `67dbd04d01bc13be2b348ecd60d668b2b529e647f48c5e336e440569960a7d40` |
| 9 | 15148 | `c596e12ab72b79d6381a1fed4ab6c6cbfb12048bee82bd4e3945d11965bc7b18` |

## Execution and acceptance

Acquire the existing per-database worker lease and recheck frozen history before
starting. Preserve earlier artifacts, all prior reservations, other allowances
and the ten non-accounting tables. Only new allowance reservations and private
receipts may change; no new production job or match row is created.

Stop immediately for transport, identity, allowance, refusal, incomplete response
or wire-schema failure. Preserve receipts, unknown usage and a typed diagnostic;
never retry automatically. Preserve completed citation-invalid responses as
failed cases without repairing their evidence, then evaluate the next case once.
Report original raw outcomes, exact citation validation and an independent
semantic reading separately. Do not treat reference-label agreement as accuracy,
unknown as compatible, partial primitives as eligible leads, or missing usage
as zero billed cost.
