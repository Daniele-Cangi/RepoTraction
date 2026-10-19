# Query diagnostic: relevant code is reachable across domains

After excluding one documented metadata-selection deviation, the unchanged
Discover GitHub reader reaches concrete implementations when given
shorter, operator-written mechanism queries. This diagnostic does **not** demonstrate
autonomous query generation, automatic source selection, semantic qualification,
or an improvement on Satellite. No paid AI calls or native experiments were made.

The most pertinent source operation found is MissNet's update of a shared latent
state using only the observation coordinates available at each time. That is a
specific code mechanism worth considering for conditional missing-link prediction;
it is not evidence that it beats Satellite's strongest direct baseline.

## Fixed scope and comparison

The user authorized a separate query diagnostic after the closed #131 trial.
`protocol.json` was written before acquiring these search results. This does not
reopen #131 or use its unused allowance. Its preparation, outputs and failure remain
unchanged at `ae0c0afd8d8765bbb94c173ff90d23ed79a526f5`.

Four free, read-only GitHub searches were made: a fresh original-query control and
three alternatives fixed beforehand. Analysis and replay were local/offline; the
new GitHub acquisitions were **not** an offline replay of the historical pool.
All used `PublicGitHub.search_repositories` with its unchanged qualifiers,
upstream ordering, first-page/20-result limit, public scope, deduplication and text
redaction. No filters, rankings, weights or search reformulations were added.

| Plain query before mandatory qualifiers | Metadata returned | First specifically eligible ranks inspected | Mechanism actually acquired in default sample |
| --- | ---: | --- | --- |
| Original: Python masked multivariate time series low rank regression cross sensor missing link prediction | 20 | None under the fixed metadata rule | Not inspected; no suitable implementation hypothesis established |
| time series matrix completion | 20 | 1, 12 | MissNet in ImputeGAP at 12; rank 1 transdim supplies only supported documentation |
| reduced rank regression | 20 | 13 | Dense reduced-rank regression in patch-seq-rrr |
| Kalman missing data | 20 | 4 | imputeTS lacks acquired R implementation; PyKalman at rank 1 was an ineligible extra inspection |

The fresh original pool shares 19/20 repository identities with the conserved #131
pool. `tangwen-qian/DailyArXiv` was replaced by `Tavish9/awesome-daily-AI-arxiv`.
This small pool drift does not establish identical historical ranking conditions.
The original still offers mostly paper collections/crawlers and sparse metadata.
Neither the old nor fresh metadata analysis proves those repositories contain no
useful source. Unknown descriptions remain unknown.

**Protocol deviation found in review:** PyKalman's supplied description states
only Kalman filter/smoother/EM, not filtering with missing observations. It was
therefore ineligible under the frozen metadata rule. Its 27 reads/24 files remain
preserved but are excluded from compliant inspection counts and mechanism yield.
`protocol-deviation.json` records the correction against the original commit.
The original protocol, selection record in `inspection.json`, source samples and
replay receipt are retained unchanged as the history of what actually happened.
They are not retroactively evidence of a compliant PyKalman selection. No query
was retried, missing metadata invented or replacement source inspected.

The inspection rule was at most the first two specific implementation hypotheses
per query, judged from metadata in upstream order, with cross-query deduplication.
There was one eligible choice for the reduced-rank query, and no forced second.
Tutorials, paper lists, visualization-only tools and unrelated software did not
qualify by matching words. These are operator judgments, not independent labels or
measured search precision. All 80 fresh metadata entries are preserved in `pools.json`.

This is a reachability diagnosis, not an equal-total-budget end-to-end contest.
The original trial chose one of up to three queries and could inspect one source.
Here the operator inspected four eligible sources across three alternatives,
plus one ineligible PyKalman source outside the rule. MissNet at
rank 12 and regression at rank 13 are outside the first three results. In the first
three, the shortened queries offer transdim (unreadable notebook implementations
under the current reader) and PyKalman (ineligible metadata; its later code mismatch is only an extra
exploratory observation).
The current one-source selector is **not shown** to choose MissNet over transdim.
Pooling these investigations must not be reported as autonomous discovery success.

## Source inspection and useful distinctions

Every selected repository used the existing default `fetch_repository` 24-file
bound. No targeted extra files, foreign code execution, package installation,
source replacement or notebook extraction followed. The supplementary catalogue
contained only paths from the same eligibility scan. Normalized samples, including
coverage limitations, are retained in `source-samples.json.gz`; pinned revisions,
blob identities, measured read costs and line references are in `inspection.json`.

- **ImputeGAP / MissNet**, revision `a18d5c5f619d05dced8348619150b4a06e138f8d`:
  `fit` creates `W = ~isnan(X)`. At each epoch, `forward_viterbi` selects both
  observed coordinates and matching loading-matrix rows before calculating the
  state update. `imputation` maps the shared latent state back to coordinates.
  This preserves information from available channels when another is absent.
  [Observed-coordinate update](https://github.com/eXascaleInfolab/ImputeGAP/blob/a18d5c5f619d05dced8348619150b4a06e138f8d/imputegap/wrapper/AlgoPython/MissNet/main.py#L195-L217).
  The file credits KoheiObata/MissNet; that upstream repository was not separately
  searched or inspected. The implementation also includes switching clusters,
  graphical-lasso fitting, interpolation initialization, EM, backward smoothing,
  isotropic model variances and filesystem checkpoints. Those are additional
  assumptions/costs, not required parts of the transferable coordinate-selection
  idea. Borrowing the whole package is not justified by this inspection.
- **patch-seq-rrr**, revision `402fe62aae4540fb61a8faf82e70ec50078fc1d6`:
  the current sklearn version learns a low-rank mapping from multivariate X to Y;
  its pure-ridge branch is particularly explicit.
  [Reduced-rank fit](https://github.com/berenslab/patch-seq-rrr/blob/402fe62aae4540fb61a8faf82e70ec50078fc1d6/sparseRRR_scikit.py#L11-L70).
  It performs dense matrix products rather than masked fitting. Complete feature
  vectors, preserving native pair support, scaling and temporal train-only model
  selection remain work. Its shuffled cross-validation must not be copied as a
  substitute for Satellite's fixed holdouts.
- **PyKalman, out-of-protocol extra inspection**, revision `d62e60be00bd028ecc7eea6a8bea02f583910428`:
  the standard correction ignores the entire observation vector when **any**
  component is masked; observation-matrix/covariance EM similarly uses complete
  rows. In the natural vector-per-epoch representation this drops the other links
  precisely where they could help. A different observation layout or update needs
  a separate test; missing-data support alone is not a suitability verdict.
  [Mask branch](https://github.com/pykalman/pykalman/blob/d62e60be00bd028ecc7eea6a8bea02f583910428/pykalman/standard.py#L260-L306).
- **transdim**, revision `eed7007ff49f83b12280844b209323e7383cc471`:
  the tree contains 65 notebooks, outside current supported file types. The reader
  acquired seven documentation files and no implementation. Implementation
  pertinence remains unknown; this is a format coverage limit, not absent code.
- **imputeTS**, revision `bca3fcd312d531a0b78c671ad0147ae086a35d0a`:
  all 48 R paths are unsupported. The acquired source-kind JavaScript files serve
  documentation and are classified as infrastructure. The imputation code remains
  uninspected. No R support or unrelated language expansion was implemented.

These findings concern source acquisition and human inspection only. We did not
run the Provider's capability/context packing, source-selection model, compatibility
assessment or native estimator. Full code acquisition does not guarantee that every
relevant operation will survive model context packing or semantic interpretation.

## Satellite interpretation

Satellite's unusual physical model is not a reason to require an RF donor. Its
conditional observation problem can be expressed as updating a shared predictive
representation from admitted channels while leaving held coordinates absent.
MissNet provides concrete code for that operation. This supports the cross-domain
search direction, with no claim that the technique is novel or inherently superior
to a direct local implementation.

Applying it would still require an independent predictive residual representation,
training-only initialization and parameter selection, correct continuity boundaries,
and the unchanged native supports and scoring. Estimated latent states/variances
must not become claims of identified physical RF sources or qualified covariance.
Backward smoothing is only admissible within the exact conditional information
boundary; it cannot be presented as whole-network future forecasting. Hidden
measurements must not enter normalization, interpolation, fitting or model choice.
No such adaptation or numerical improvement was measured here.

There is also still no independently established practical failure attached to
#131's operator-selected 10% improvement threshold. Finding relevant code does not
repair that weakness in case selection or demonstrate that an agent was unblocked.

## Cost, checks and conclusion

Four search reads plus 85 source metadata/tree/blob reads acquired 70 files,
635,670 bytes of accepted source text. The four search-operation durations sum to
10.983 s and five source-acquisition durations to 80.394 s. Operations ran
concurrently; these sums are not end-to-end wall time and exclude human inspection.
They are not comparable to the historical paid job's total latency.
These actual costs include the ineligible PyKalman inspection: 27 source reads,
24 files, 268,720 bytes. The compliant subset has 58 source reads, 46 files and
366,950 bytes; both subsets are reported, with no work hidden from accounting.

All four search pools and five source samples were replayed offline through the
unchanged reader. Outputs were identical, except the source acquisition timestamp;
all received Git blob identities were recalculated from their raw bytes locally.
`offline-replay.json` records those checks. Raw HTTP captures stay in the ignored
local diagnostic directory; the public bundle contains only reader-normalized
outputs and does not introduce a runner, cache or audit subsystem.

Existing request-led discovery regressions: **20 passed**. Product code and Satellite
working trees are unchanged. No paid calls, no native runs, no new qualified links.

The supported conclusion is narrow: the original query was not enough to expose
useful code in its bounded metadata pool, and short mechanism queries can reach
pertinent code with the existing reader. Satellite-specific repository scarcity
does not prevent that. The experiment does not establish a general query policy or
justify a new search framework, automatic query retries, notebook/R support, more
candidates, or a larger source-inspection budget.

The two compliant source samples with relevant mechanism code are MissNet and
patch-seq-rrr. PyKalman must not be counted as a third compliant result.

For a subsequent native transfer trial, the one specific mechanism I would carry
forward is **updating shared predictive state from observed coordinates only**,
with MissNet's lines as a concrete reference. First establish a genuinely failed
practical criterion and keep the strongest direct comparator. If the operator
supplies this mechanism, call the experiment assisted transfer; autonomous search
requires the system itself to choose the query/source. This diagnostic alone
cannot receive credit for either native benefit or autonomy.
