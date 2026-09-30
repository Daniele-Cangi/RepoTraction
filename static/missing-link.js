/* Public material is data, not HTML, instructions or permission to run code. */
export function safeGithubUrl(value) {
  try {
    const url = new URL(String(value || ""));
    if (url.protocol !== "https:" || url.hostname !== "github.com" || url.port || url.username || url.password) return "";
    return url.href;
  } catch {
    return "";
  }
}

export function normalizeRepository(value) {
  const name = String(value || "").trim();
  return /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\/[A-Za-z0-9_.-]{1,100}$/.test(name) ? name : "";
}

const CLASSIFICATIONS = {
  direct: ["Existing interface", "direct"],
  adapter: ["Narrow adapter needed", "adapter"],
  extraction: ["Internal capability · extraction needed", "extraction"],
  rejected: ["Not a fit", "rejected"],
  investigate: ["Needs investigation", "investigate"],
};
const CHECKS = {
  satisfied: ["Supported by evidence", "satisfied"],
  incompatible: ["Incompatible", "incompatible"],
  undetermined: ["Not established", "undetermined"],
};
const DISCOVERY = {
  external_lead: "Potential external connection · novelty unverified",
  known_reference: "Already referenced · not a new discovery",
  reference_review: "Package reference hint · verify identity and intent",
  same_project: "Same-project work · not an external discovery",
  reference_only: "Reference note / demand not established",
  not_actionable: "Actionable independent demand not established",
  not_a_fit: "Not a usable connection",
  partial_contribution: "Partial code support · full request still rejected",
  similarity_only: "Retrieval similarity only · contribution not demonstrated",
  needs_review: "Discovery qualification needs review",
};
const VERIFICATIONS = {
  not_executed: "Not executed",
  fixture: "Fixture test only",
  integration: "Integration test",
  live: "Live-context test",
};
const ACTIVE_JOBS = new Set(["queued", "running"]);

export function initMissingLink({ api, escapeHtml, demoMode, getDashboard }) {
  const root = document.querySelector("#missingLinkRoot");
  const e = escapeHtml;
  const state = {
    active: false, data: null, account: null, loading: false, pending: false,
    timer: null, filter: "all", includeSuperseded: false, reviewedRevision: null, importJob: "", lastRendered: {},
  };
  const find = (id) => root.querySelector(`#${id}`);
  const array = (value) => Array.isArray(value) ? value : [];
  const text = (value) => typeof value === "string" ? value : value == null ? "" : JSON.stringify(value);
  const standalone = (value) => value === true || value === "yes" ? "yes" : value === false || value === "no" ? "no" : "unknown";
  const selectedRepo = () => normalizeRepository(find("mlRepo")?.value);
  const matchingRepo = () => array(state.data?.repositories).find((repo) =>
    String(repo.full_name || repo.repo || "").toLowerCase() === selectedRepo().toLowerCase());
  const repoKey = () => `${selectedRepo().toLowerCase()}:${matchingRepo()?.revision || ""}:${JSON.stringify(matchingRepo()?.capabilities || [])}`;
  const reviewed = () => state.reviewedRevision === repoKey() && Boolean(matchingRepo()?.capabilities?.length);
  const link = (url, label) => safeGithubUrl(url)
    ? `<a href="${e(safeGithubUrl(url))}" target="_blank" rel="noreferrer">${e(label)} ↗</a>`
    : `<span>${e(label)}</span>`;
  const list = (values, empty = "Not established.") => array(values).length
    ? `<ul>${values.map((value) => `<li>${e(text(value))}</li>`).join("")}</ul>`
    : `<p class="ml-muted">${e(empty)}</p>`;
  const evidence = (values) => array(values).length
    ? `<ul class="ml-evidence">${values.map((item) => {
      const label = item.path ? `${item.path}${item.line ? `:${item.line}` : ""}` : item.kind || "Source";
      return `<li>${link(item.url, label)}${item.kind ? `<small>${e(item.kind)}</small>` : ""}${item.quote ? `<blockquote>${e(item.quote)}</blockquote>` : ""}</li>`;
    }).join("")}</ul>`
    : '<p class="ml-muted">No supporting source supplied.</p>';
  const note = (message, isError = false) => {
    const target = find("mlNotice");
    if (!target) return;
    target.textContent = message;
    target.classList.toggle("ml-error", isError);
    target.classList.toggle("hidden", !message);
  };

  if (demoMode) {
    root.innerHTML = `<article class="panel-card ml-demo">
      <span class="ml-kicker">Public capability discovery</span><h3>Missing Link works with real public source evidence</h3>
      <p>Choose a repository, review its code-backed capabilities, and compare them with a public GitHub request. Every result separates requirements, obstacles, existing code and new bridge work.</p>
      <div class="ml-flow" aria-label="Discovery flow"><span>Problem</span><b>→</b><span>Capability</span><b>→</b><span>Bridge</span><b>→</b><span>Evidence</span></div>
      <p class="ml-callout">Discovery is disabled in this synthetic demo. No demands, matches or successful proofs have been invented for a screenshot.</p>
      <a class="button button-primary" href="/#missing-link">Open live Missing Link</a>
      <p class="ml-muted">Public repositories only. No automatic comments or pull requests. Downloaded or generated code is never run in this dashboard.</p>
    </article>`;
    return { setActive() {}, updateDashboard() {} };
  }

  root.innerHTML = `
    <div id="mlNotice" class="ml-notice hidden" role="status" aria-live="polite"></div>
    <article class="panel-card ml-workbench">
      <div class="card-heading"><div><p class="eyebrow">1 · Select public source</p><h3>A repository and a real need</h3></div><button class="button button-secondary" type="button" data-ml-action="refresh">Refresh results</button></div>
      <p class="ml-muted">Starts from code, not stars or traffic. GitHub API requests are bounded and cached; an empty search is not proof that no demand exists.</p>
      <form id="mlStartForm">
        <div class="ml-form-grid">
          <label class="ml-field ml-wide"><span>Public repository</span><input id="mlRepo" name="repo" list="mlPublicRepositories" required maxlength="140" placeholder="owner/repository" autocomplete="off" spellcheck="false" /><datalist id="mlPublicRepositories"></datalist><small>Choose one of your public repositories or enter another public owner/repository.</small></label>
          <label class="ml-field"><span>GitHub API request limit</span><input id="mlMaxRequests" type="number" min="10" max="200" value="80" required /><small>Maximum per job; includes source and discussion requests.</small></label>
          <label class="ml-field"><span>Candidate limit</span><input id="mlMaxCandidates" type="number" min="1" max="10" value="5" required /><small>Small, reviewable discovery batches.</small></label>
        </div>
        <div class="ml-actions"><button id="mlAnalyzeButton" class="button button-secondary" type="button" data-ml-action="analyze">Analyze repository</button><span id="mlAnalyzeHint" class="ml-muted">Review capabilities before matching a request.</span></div>
        <div class="ml-divider"></div>
        <label class="ml-check"><input id="mlReviewed" type="checkbox" disabled /><span>I reviewed the capabilities and their source coverage below.</span></label>
        <div class="ml-form-grid ml-request-fields">
          <label class="ml-field ml-wide"><span>Specific public request <small>optional</small></span><input id="mlIssue" type="url" maxlength="400" placeholder="https://github.com/owner/repository/issues/123" autocomplete="off" /><small>Leave empty for discovery. The full available discussion is checked, not just the title.</small></label>
          <label class="ml-field ml-wide"><span>Discovery query <small>optional</small></span><input id="mlQuery" maxlength="220" placeholder="A problem or mechanism, not just the project name" autocomplete="off" /><small>Leave empty to derive searches from the reviewed capabilities.</small></label>
        </div>
        <div id="mlProvider" class="ml-provider"><p class="ml-muted">Checking optional AI configuration…</p></div>
        <label class="ml-check"><input id="mlUseAI" type="checkbox" disabled /><span>Use the configured AI provider within its configured limits <small>off by default</small></span></label>
        <div class="ml-actions"><button id="mlDiscoverButton" class="button button-primary" type="submit" disabled>Find relevant requests</button><span class="ml-muted">No third-party publication. No code execution.</span></div>
      </form>
    </article>
    <section class="ml-section" aria-label="Requirement compatibility results">
      <div class="card-heading"><div><p class="eyebrow">Problem → capability → bridge</p><h3>Compatibility, not resemblance</h3></div><span id="mlMatchCount" class="count-pill">0 results</span></div>
      <div id="mlFilters" class="ml-filters" aria-label="Result classification"><button class="filter active" type="button" data-ml-filter="all">All</button><button class="filter" type="button" data-ml-filter="direct">Existing interface</button><button class="filter" type="button" data-ml-filter="adapter">Adapter</button><button class="filter" type="button" data-ml-filter="extraction">Extraction</button><button class="filter" type="button" data-ml-filter="investigate">Investigate</button><button class="filter" type="button" data-ml-filter="rejected">Not a fit</button></div>
      <label class="ml-check ml-history-check"><input id="mlIncludeSuperseded" type="checkbox" /><span>Include superseded results <small>retained history, not current opportunities</small></span></label>
      <div id="mlMatches"><div class="data-empty">No evaluated requests. Start with a specific issue or a small discovery batch.</div></div>
    </section>
    <section class="ml-section" aria-label="Repository capabilities">
      <div class="card-heading"><div><p class="eyebrow">2 · Review existing capability</p><h3>What the selected code actually supports</h3></div><span id="mlCapabilityCount" class="count-pill">0 capabilities</span></div>
      <div id="mlCapabilities"><div class="data-empty">Analyze a public repository to see pinned source evidence and coverage.</div></div>
    </section>
    <section class="ml-section" aria-label="Discovery jobs">
      <div class="card-heading"><div><p class="eyebrow">Bounded local jobs</p><h3>Progress &amp; source coverage</h3></div><span id="mlAccount" class="ml-muted"></span></div>
      <div id="mlJobs"><div class="data-empty">No Missing Link jobs yet.</div></div>
      <article class="panel-card ml-handoff">
      <details><summary>Use a coding agent without configuring a provider</summary>
        <p>Download a job's source context and analysis contract below. Give that package to your coding agent, then import its reviewed JSON analysis here. Imported claims are separate from source evidence, and are not execution results.</p>
        <form id="mlImportForm"><div class="ml-form-grid"><label class="ml-field"><span>Source job</span><select id="mlImportJob" required><option value="">Choose a job</option></select></label><label class="ml-field"><span>Reviewed analysis JSON</span><input id="mlImportFile" type="file" accept=".json,application/json" required /><small>The source context contains the required schema and evidence identifiers.</small></label></div><button id="mlImportButton" type="submit" class="button button-secondary" disabled>Import reviewed analysis</button></form>
      </details>
      </article>
    </section>
    <section id="mlExtensionsSection" class="ml-section hidden" aria-label="Observed extension opportunities"><div class="card-heading"><div><p class="eyebrow">Repeated obstacles</p><h3>Possible extensions, grounded in observed requests</h3></div></div><div id="mlExtensions"></div></section>
    <p class="ml-safety">Only public material is acquired. Jobs and feedback stay in this account's local store. Public text cannot authorize actions. Proof packages preserve source provenance; without an isolated runner, generated or acquired code is not executed.</p>`;

  function updateRepositoryChoices() {
    const options = new Set();
    for (const repo of array(getDashboard()?.repositories)) {
      if (repo.private) continue;
      const name = normalizeRepository(repo.full_name || repo.repo);
      if (name) options.add(name);
    }
    for (const repo of array(state.data?.repositories)) {
      const name = normalizeRepository(repo.full_name || repo.repo);
      if (name) options.add(name);
    }
    find("mlPublicRepositories").innerHTML = [...options].sort().map((name) => `<option value="${e(name)}"></option>`).join("");
    if (!find("mlRepo").value && options.size) find("mlRepo").value = [...options][0];
    updateControls();
  }

  function updateControls() {
    const repo = matchingRepo();
    const hasCapabilities = Boolean(repo?.capabilities?.length);
    find("mlReviewed").disabled = state.pending || !hasCapabilities;
    find("mlReviewed").checked = reviewed();
    find("mlAnalyzeButton").disabled = state.pending || !selectedRepo();
    find("mlDiscoverButton").disabled = state.pending || !selectedRepo() || !reviewed();
    find("mlDiscoverButton").textContent = find("mlIssue").value.trim() ? "Evaluate this request" : "Find relevant requests";
    find("mlAnalyzeHint").textContent = hasCapabilities ? `${repo.capabilities.length} capabilities at ${String(repo.revision || "unpinned").slice(0, 12)} · review below` : "Analyze source, then review capabilities before matching.";
    const configured = Boolean(state.data?.provider?.configured);
    find("mlUseAI").disabled = state.pending || !configured;
    if (!configured) find("mlUseAI").checked = false;
    find("mlImportButton").disabled = state.pending || !find("mlImportJob").value || !find("mlImportFile").files?.length;
    for (const button of root.querySelectorAll('[data-ml-action="cancel"], [data-ml-action="resume"]')) {
      const job = array(state.data?.jobs).find((item) => item.id === button.dataset.jobId);
      const limit = Number(job?.input?.max_requests || 80);
      const exhausted = job && Number(job.requests_used) >= limit;
      button.disabled = state.pending || (button.dataset.mlAction === "resume" && exhausted && Number(find("mlMaxRequests").value) <= limit);
    }
  }

  function replacePreservingDetails(id, html, fingerprint) {
    if (state.lastRendered[id] === fingerprint) return;
    const target = find(id);
    if (target.contains(document.activeElement) && document.activeElement.matches("input, textarea, select")) return;
    const opened = new Set([...target.querySelectorAll("details[open][data-ml-detail]")].map((node) => node.dataset.mlDetail));
    target.innerHTML = html;
    for (const node of target.querySelectorAll("details[data-ml-detail]")) node.open = opened.has(node.dataset.mlDetail);
    state.lastRendered[id] = fingerprint;
  }

  function renderCapabilities() {
    const repo = matchingRepo();
    const capabilities = array(repo?.capabilities);
    find("mlCapabilityCount").textContent = `${capabilities.length} capabilities`;
    if (!repo) {
      replacePreservingDetails("mlCapabilities", '<div class="data-empty">Analyze the selected public repository to inspect pinned source evidence.</div>', selectedRepo());
      return;
    }
    const coverage = repo.coverage || {};
    const sourceHeader = `<article class="ml-coverage"><strong>${e(repo.full_name || repo.repo)} <code>${e(String(repo.revision || "Unpinned revision").slice(0, 12))}</code></strong><p>${e(typeof coverage === "string" ? coverage : coverage.summary || coverage.description || "Source analysis is bounded. Coverage is not a claim that every mechanism has been found.")}</p><details data-ml-detail="coverage"><summary>Analysis coverage &amp; limits</summary><pre>${e(typeof coverage === "string" ? coverage : JSON.stringify(coverage, null, 2))}</pre></details></article>`;
    const capabilityCards = capabilities.map((capability) => `<article class="ml-capability">
        <div class="ml-card-top"><span class="ml-pill">${e(capability.level || "Capability")}</span><span class="ml-muted">${e(capability.claim_source || "source analysis")}</span></div>
        <h4>${e(capability.name)}</h4><p>${e(capability.summary || capability.outcome)}</p>
        <dl class="ml-facts"><div><dt>Outcome</dt><dd>${e(capability.outcome || "Not established")}</dd></div><div><dt>Entry point</dt><dd><code>${e(text(capability.entrypoint) || "Internal / not established")}</code></dd></div><div><dt>Separately reusable</dt><dd>${standalone(capability.standalone) === "yes" ? "Reported as standalone; verify the context below" : standalone(capability.standalone) === "no" ? "No · coupling / extraction must be checked" : "Not established"}</dd></div><div><dt>Test coverage</dt><dd>${e(capability.test_coverage === "referenced" ? "Tests referenced · not executed" : capability.test_coverage === "none" ? "No test reference found in the analyzed subset" : text(capability.test_coverage) || "Not established; source presence is not a passing test")}</dd></div></dl>
        <details data-ml-detail="cap-${e(capability.id)}"><summary>Inputs, dependencies, obstacles &amp; source evidence</summary><h5>Inputs</h5>${list(capability.inputs)}<h5>Outputs</h5>${list(capability.outputs)}<h5>Dependencies / preconditions</h5>${list([...array(capability.dependencies), ...array(capability.preconditions)])}<h5>Limitations</h5>${list(capability.limitations)}${evidence(capability.evidence)}</details>
        <details data-ml-detail="correction-${e(capability.id)}"><summary>Correct this capability as maintainer</summary><p class="ml-muted">Your correction is recorded separately. It does not rewrite source evidence or certify a test.</p>
          <form class="ml-correction-form" data-capability-id="${e(capability.id)}">
            <label class="ml-field"><span>Name</span><input name="name" value="${e(capability.name)}" maxlength="160" required /></label>
            <label class="ml-field"><span>Summary</span><textarea name="summary" maxlength="3000" rows="3">${e(capability.summary)}</textarea></label>
            <label class="ml-field"><span>Outcome</span><textarea name="outcome" maxlength="2000" rows="2">${e(capability.outcome)}</textarea></label>
            <label class="ml-field"><span>Problem / mechanism search terms <small>one per line</small></span><textarea name="search_terms" maxlength="2000" rows="3">${e(array(capability.search_terms).join("\n"))}</textarea></label>
            <label class="ml-field"><span>Preconditions <small>one per line</small></span><textarea name="preconditions" maxlength="3000" rows="2">${e(array(capability.preconditions).join("\n"))}</textarea></label>
            <label class="ml-field"><span>Limitations <small>one per line</small></span><textarea name="limitations" maxlength="3000" rows="2">${e(array(capability.limitations).join("\n"))}</textarea></label>
            <label class="ml-field"><span>Standalone claim</span><select name="standalone"><option value="unknown" ${standalone(capability.standalone) === "unknown" ? "selected" : ""}>Not established</option><option value="yes" ${standalone(capability.standalone) === "yes" ? "selected" : ""}>Separately reusable</option><option value="no" ${standalone(capability.standalone) === "no" ? "selected" : ""}>Coupled / extraction needed</option></select></label>
            <button class="button button-secondary" type="submit">Save maintainer correction</button>
          </form>
        </details>
      </article>`);
    const html = `${sourceHeader}<div class="ml-capability-grid">${capabilityCards.slice(0, 3).join("")}</div>
      ${capabilityCards.length > 3 ? `<details class="ml-more-capabilities" data-ml-detail="more-capabilities-${e(repo.full_name || repo.repo)}-${e(repo.revision)}"><summary>Review ${capabilityCards.length - 3} additional capabilities · all source evidence and corrections remain available</summary><div class="ml-capability-grid">${capabilityCards.slice(3).join("")}</div></details>` : ""}
      ${!capabilities.length ? '<p class="ml-callout">No capability was established in the analyzed subset. Review the coverage or use a coding-agent source package; this is not a claim that the repository has no useful code.</p>' : ""}`;
    replacePreservingDetails("mlCapabilities", html, JSON.stringify(repo));
    updateControls();
  }

  function renderProvider() {
    const provider = state.data?.provider || {};
    find("mlProvider").innerHTML = provider.configured
      ? `<strong>Optional AI · ${e(provider.kind || "configured provider")}${provider.model ? ` / ${e(provider.model)}` : ""}</strong><p>${e(provider.remote ? "Remote provider: public source excerpts and discussion context leave your machine only when you opt in." : "Provider configuration is available. Review its endpoint and outbound data before opting in.")}</p><p>${e(provider.outbound_description || "Only selected public source excerpts and issue context are sent; never GitHub credentials.")}</p><small>Configured limits: ${e(text(provider.limits) || "See local provider configuration")}</small>`
      : `<strong>No AI provider configured · no paid calls</strong><p>The conservative local lane gathers pinned source and public discussion context. Requirements still need interpretive review; unverified matches remain “Needs investigation”. Use a source-context handoff with your coding agent for deeper analysis, or configure an optional provider.</p>${provider.error ? `<p class="ml-error">Configuration: ${e(provider.error)}</p>` : ""}`;
  }

  function renderJobs() {
    const jobs = array(state.data?.jobs);
    find("mlAccount").textContent = state.account ? `Local account: ${state.account}` : "Local account";
    const html = jobs.length ? jobs.map((job) => {
      const status = ["queued", "running", "completed", "cancelled", "failed", "paused"].includes(job.status) ? job.status : "unknown";
      const result = job.result || {};
      const progress = Number.isFinite(Number(job.progress)) ? `${Number(job.progress)}%` : text(job.progress);
      const limit = Number(job.input?.max_requests || 80);
      const exhausted = Number(job.requests_used) >= limit;
      return `<article class="ml-job"><div class="ml-card-top"><strong>${e(job.input?.repo || job.repo || "Public source job")}</strong><span class="ml-pill ${status}">${e(status)}</span></div>
        <p>${e(job.stage || "Preparing")}${progress ? ` · ${e(progress)}` : ""}</p><small>${Number(job.requests_used) || 0} GitHub requests · ${Number(job.ai_calls_used) || 0} AI calls · ${e(job.created_at || "")}</small>
        ${job.error ? `<p class="ml-error">${e(job.error)}</p>` : ""}
        ${result.partial ? `<div class="ml-callout"><strong>Partial investigation · ${array(result.candidate_errors).length} candidate validation failure(s)</strong><p>Other candidates were processed. Invalid analysis was not accepted; charged usage is retained. No automatic retry.</p>${list(array(result.candidate_errors).map((failure) => `${failure.url || "Candidate"} · ${failure.stage || "analysis"}: ${failure.error || "Validation failed"}`))}</div>` : ""}
        ${result.warning || result.incompleteness ? `<p class="ml-callout">${e(text(result.warning || result.incompleteness))}</p>` : ""}
        ${array(result.warnings).length ? `<div class="ml-callout">${list(result.warnings)}</div>` : ""}
        ${exhausted && ["cancelled", "paused", "failed"].includes(status) ? `<p class="ml-callout">This job used its ${limit}-request budget. ${limit >= 200 ? "The per-job maximum is reached; start a separate, smaller investigation." : "To resume, explicitly increase the request limit in the controls above. The higher limit is the total job budget, not an additional allowance."}</p>` : ""}
        <div class="ml-actions">${ACTIVE_JOBS.has(status) ? `<button class="button button-secondary" type="button" data-ml-action="cancel" data-job-id="${e(job.id)}">Cancel job</button>` : ["cancelled", "paused", "failed"].includes(status) && !(exhausted && limit >= 200) ? `<button class="button button-secondary" type="button" data-ml-action="resume" data-job-id="${e(job.id)}">${exhausted ? "Resume with higher request limit" : "Resume within remaining budget"}</button>` : ""}<a class="button button-secondary" href="/api/missing-link/context?job_id=${encodeURIComponent(job.id)}">Download source context</a></div>
        <details data-ml-detail="job-${e(job.id)}"><summary>Collection details and limitations</summary><pre>${e(JSON.stringify(result, null, 2))}</pre></details>
      </article>`;
    }).join("") : '<div class="data-empty">No Missing Link jobs yet. Existing analytics do not depend on this feature.</div>';
    replacePreservingDetails("mlJobs", html, JSON.stringify(jobs));
    const previous = find("mlImportJob").value;
    find("mlImportJob").innerHTML = '<option value="">Choose a job</option>' + jobs.filter((job) => !ACTIVE_JOBS.has(job.status)).map((job) => `<option value="${e(job.id)}">${e(job.input?.repo || job.repo || "Source job")} · ${e(job.stage || job.status)} · ${e(String(job.id).slice(0, 8))}</option>`).join("");
    if (jobs.some((job) => job.id === previous && !ACTIVE_JOBS.has(job.status))) find("mlImportJob").value = previous;
  }

  function renderMatches() {
    const selected = matchingRepo();
    const all = array(state.data?.matches).filter((match) =>
      (!selectedRepo() || (selected?.id != null && match.repo_id != null && String(match.repo_id) === String(selected.id)))
      && (state.includeSuperseded || !(match.superseded === true || match.status === "superseded")));
    const matches = all.filter((match) => state.filter === "all" || match.classification === state.filter);
    find("mlMatchCount").textContent = `${all.length} results for selected repository`;
    for (const button of find("mlFilters").querySelectorAll("button")) {
      const active = button.dataset.mlFilter === state.filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
    const html = matches.length ? matches.map((match) => {
      const [classification, tone] = CLASSIFICATIONS[match.classification] || CLASSIFICATIONS.investigate;
      const request = match.request || {};
      const bridge = match.bridge || {};
      const verification = bridge.verification || { status: "not_executed" };
      const examples = array(match.isolated_examples);
      const currentExamples = examples.filter((example) => example.applies_to_current_bridge === true);
      const capability = match.capability || array(selected?.capabilities).find((item) => item.id === match.capability_id);
      const revisionChanged = selected?.revision && match.revision && selected.revision !== match.revision;
      const feedbackHistory = array(match.feedback);
      const latestFeedback = feedbackHistory.length ? feedbackHistory[feedbackHistory.length - 1] : match.feedback || {};
      const checks = array(match.checks);
      const discovery = match.discovery_assessment || {};
      const unknownHard = array(request.requirements).filter((requirement) => requirement.mandatory && checks.find((check) => check.requirement_id === requirement.id)?.status !== "satisfied");
      return `<article class="ml-match ${tone}">
        <div class="ml-card-top"><span class="ml-pill ${tone}">${classification}</span><span class="ml-muted">${e(match.analysis_source || match.claim_source || "Conservative source analysis")}</span></div>
        <p class="ml-callout">${e(DISCOVERY[discovery.status] || "Discovery not assessed · novelty unverified")}</p>
        ${match.superseded === true || match.status === "superseded" ? '<p class="ml-callout">Superseded result · retained for audit and export, not a current opportunity.</p>' : ""}
        <p class="ml-kicker">Publicly expressed problem</p><h4>${link(request.url, request.title || request.outcome || "Public request")}</h4>
        ${request.outcome ? `<p>${e(request.outcome)}</p>` : ""}<p class="ml-muted">Discussion: ${e(request.status || "unknown")} · ${request.context_complete === true ? "Available context collected" : "Context incomplete / not established"}</p>
        <div class="ml-problem-bridge"><div><span>Existing capability</span><strong>${e(capability?.name || match.capability_id || "Not established")}</strong><small>${e(match.repo)} · ${e(String(match.revision || "").slice(0, 12))}</small></div><b aria-hidden="true">→</b><div><span>Technical bridge</span><strong>${e(bridge.summary || match.summary || "No bridge established")}</strong><small>${e(bridge.kind || classification)}</small></div></div>
        <p>${e(match.summary || "Compatibility is not yet established.")}</p>
        ${revisionChanged || match.stale === true ? '<p class="ml-callout">The repository source, capability interpretation, request discussion or analysis contract changed after this result. This is historical evidence; reevaluate against the current evidence before adopting the bridge.</p>' : ""}
        ${unknownHard.length ? `<p class="ml-callout">${unknownHard.length} mandatory requirement${unknownHard.length === 1 ? " is" : "s are"} not supported. Similar wording does not establish a usable fit.</p>` : ""}
        ${match.discovery_assessment ? `<details data-ml-detail="discovery-${e(match.id)}"><summary>Discovery qualification · separate from technical compatibility</summary>${list(discovery.reasons)}${discovery.supported_requirement_ids ? `<p>Existing support: ${array(discovery.supported_requirement_ids).length} requirements · Conflicts: ${array(discovery.conflicting_requirement_ids).length} · Undetermined: ${array(discovery.undetermined_requirement_ids).length}. Partial support does not establish complete fulfillment.</p>` : ""}<p class="ml-muted">Novelty is unverified. Source-reference hints are not evidence of adoption or endorsement.</p>${array(discovery.references).map((ref) => `<section>${link(ref.url, ref.source_id || "Discussion source")}<small> · ${e(ref.kind || "Reference hint")}</small><blockquote>${e(ref.quote)}</blockquote></section>`).join("")}</details>` : ""}
        <div class="ml-result-columns"><div><h5>Adoption obstacles</h5>${list(match.obstacles, "No obstacle was supplied; that is not proof of frictionless adoption.")}</div><div><h5>Proof status</h5><span class="ml-pill investigate">${e(currentExamples.length ? (currentExamples[0].status === "exited_successfully" ? "Isolated example ran" : "Isolated example did not pass") : VERIFICATIONS[verification.status] || "Not executed / unknown")}</span><p>${e(examples.length ? "Runner receipts below are separate from model claims. Original request compliance and target integration remain unverified; historical receipts do not verify a changed bridge." : verification.reason || "Source inspection alone is not a successful execution. No downloaded or generated code is run automatically.")}</p></div></div>
        ${examples.length ? `<details data-ml-detail="examples-${e(match.id)}"><summary>Isolated WASI examples · ${examples.length} run(s), not target integration</summary>${examples.map((example) => `<section><h5>${e(example.status)} · ${e(example.entrypoint)}${example.applies_to_current_bridge ? "" : " · historical artifact"}</h5><p class="ml-muted">${e(example.at)} · pinned revision ${e(String(example.revision).slice(0, 12))} · request criteria not automatically verified</p><pre>${e(example.stdout || example.stderr || "No output")}</pre>${list(example.limitations)}<details><summary>Runtime limits and artifact hashes</summary><pre>${e(JSON.stringify({isolation: example.isolation, artifact_sha256: example.artifact_sha256}, null, 2))}</pre></details></section>`).join("")}</details>` : ""}
        <details data-ml-detail="requirements-${e(match.id)}"><summary>Every requirement &amp; its evidence</summary><div class="ml-requirements">${array(request.requirements).map((requirement) => {
          const check = checks.find((item) => item.requirement_id === requirement.id) || {};
          const [label, checkTone] = CHECKS[check.status] || CHECKS.undetermined;
          const source = requirement.source || {};
          return `<section class="ml-requirement"><div class="ml-card-top"><span class="ml-pill ${checkTone}">${label}</span><small>${requirement.mandatory ? "Mandatory constraint" : "Preference / contextual requirement"} · ${requirement.explicit === true ? "Explicit in source" : "Inferred / requires confirmation"}</small></div><h5>${e(requirement.text)}</h5><p>${e(check.reason || "No supporting check supplied.")}</p>${source.quote || requirement.quote ? `<blockquote>${e(source.quote || requirement.quote)}</blockquote>` : ""}${source.url ? link(source.url, "Request source") : ""}${evidence(check.evidence)}</section>`;
        }).join("") || '<p class="ml-muted">No independently extracted requirements yet.</p>'}</div><h5>Missing information</h5>${list(request.missing_information, "No missing information was supplied.")}</details>
        <details data-ml-detail="bridge-${e(match.id)}"><summary>Bridge steps, success criteria &amp; reproducible files</summary>
          <h5>Success criteria from the request</h5>${list(bridge.success_criteria)}<h5>Existing code contribution</h5><p>${e(text(bridge.existing_contribution) || "Not established")}</p><h5>New logic / adaptation</h5><p>${e(text(bridge.new_logic) || "Not established")}</p><h5>Bridge steps</h5>${list(bridge.steps)}<h5>Assumptions</h5>${list(bridge.assumptions)}
          ${array(bridge.files).map((file) => `<details data-ml-detail="file-${e(match.id)}-${e(file.path)}"><summary>${e(file.path)}</summary><pre><code>${e(file.content)}</code></pre></details>`).join("")}
          <p class="ml-callout">A package is an inspection and reproduction handoff, not a certificate of execution. Review licensing, revisions, inputs and isolation requirements before running any included code.</p>
        </details>
        <div class="ml-actions"><a class="button button-secondary" href="/api/missing-link/export?match_id=${encodeURIComponent(match.id)}">Download agent handoff .json</a><a class="button button-secondary" href="/api/missing-link/package?match_id=${encodeURIComponent(match.id)}">Download proof package .zip</a></div>
        <details data-ml-detail="feedback-${e(match.id)}"><summary>Maintainer feedback${latestFeedback.decision ? ` · ${e(latestFeedback.decision)}` : ""}</summary><p class="ml-muted">Feedback does not alter the original request or certify compatibility.</p>${feedbackHistory.length ? `<ul>${feedbackHistory.map((item) => `<li><strong>${e(item.decision)}</strong>${item.note ? ` · ${e(item.note)}` : ""}<small> · ${e(item.at || "")}</small></li>`).join("")}</ul>` : ""}<form class="ml-feedback-form" data-match-id="${e(match.id)}"><label class="ml-field"><span>Your assessment</span><select name="decision"><option value="relevant" ${latestFeedback.decision === "relevant" ? "selected" : ""}>Relevant</option><option value="needs_work" ${latestFeedback.decision === "needs_work" ? "selected" : ""}>Needs work</option><option value="rejected" ${latestFeedback.decision === "rejected" ? "selected" : ""}>Reject this match</option></select></label><label class="ml-field"><span>Reason / missing bridge work</span><textarea name="note" rows="3" maxlength="3000">${e(latestFeedback.note || "")}</textarea></label><button type="submit" class="button button-secondary">Save feedback</button></form></details>
      </article>`;
    }).join("") : `<div class="data-empty">${all.length ? "No results in this classification." : "No evaluated requests for this repository. An empty batch is not evidence of no demand."}</div>`;
    replacePreservingDetails("mlMatches", html, JSON.stringify([matches, state.filter, selectedRepo()]));
  }

  function renderExtensions() {
    const groups = array(state.data?.extension_groups);
    find("mlExtensionsSection").classList.toggle("hidden", !groups.length);
    const html = groups.map((group) => `<article class="ml-extension"><strong>${e(group.requirement)}</strong><p>${Number(group.count) || array(group.match_ids).length} observed request(s) blocked by this requirement. This is an extension lead, not a forecast of adoption.</p><small>Evidence: ${e(array(group.match_ids).join(", "))}</small></article>`).join("");
    replacePreservingDetails("mlExtensions", html, JSON.stringify(groups));
  }

  function render() {
    updateRepositoryChoices();
    renderProvider();
    renderCapabilities();
    renderJobs();
    renderMatches();
    renderExtensions();
    updateControls();
  }

  function schedule() {
    clearTimeout(state.timer);
    state.timer = null;
    if (state.active && array(state.data?.jobs).some((job) => ACTIVE_JOBS.has(job.status))) {
      state.timer = setTimeout(() => refresh(), 4500);
    }
  }

  function clearAccountState() {
    state.reviewedRevision = null;
    state.lastRendered = {};
    state.data = null;
    find("mlRepo").value = "";
    find("mlIssue").value = "";
    find("mlQuery").value = "";
    find("mlImportFile").value = "";
    find("mlUseAI").checked = false;
  }

  async function refresh() {
    if (!state.active || state.loading) return;
    state.loading = true;
    try {
      const data = await api("/api/missing-link");
      const account = text(data.account?.login || data.account);
      if (state.account && state.account !== account) {
        clearAccountState();
        note("GitHub account changed. Missing Link now shows only the current account's local results.");
      }
      state.account = account;
      state.data = data;
      render();
    } catch (error) {
      note(error.message, true);
    } finally {
      state.loading = false;
      schedule();
    }
  }

  async function post(path, body, successMessage) {
    if (state.pending) return;
    state.pending = true;
    note("");
    updateControls();
    try {
      await api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (successMessage) note(successMessage);
      state.lastRendered = {};
      await refresh();
    } catch (error) {
      note(error.message, true);
    } finally {
      state.pending = false;
      updateControls();
    }
  }

  function jobInput(action) {
    const repo = selectedRepo();
    if (!repo) throw new Error("Enter a public repository as owner/repository.");
    if (!find("mlMaxRequests").reportValidity() || !find("mlMaxCandidates").reportValidity()) return null;
    const body = {
      repo, max_requests: Number(find("mlMaxRequests").value), max_candidates: Number(find("mlMaxCandidates").value),
      use_ai: Boolean(find("mlUseAI").checked && state.data?.provider?.configured),
    };
    if (action === "analyze") body.action = "analyze";
    else {
      if (!reviewed()) throw new Error("Review the pinned capabilities, then check the review box before matching.");
      const issue = find("mlIssue").value.trim();
      if (issue) {
        const url = safeGithubUrl(issue);
        if (!url || !/^\/[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+\/issues\/[1-9][0-9]*$/.test(new URL(url).pathname)) throw new Error("Use a public GitHub issue URL: https://github.com/owner/repository/issues/123.");
        if (new URL(url).search || new URL(url).hash) throw new Error("Use a public GitHub issue URL without query or fragment.");
        body.issue_url = url;
      }
      const query = find("mlQuery").value.trim();
      if (query) body.query = query;
    }
    return body;
  }

  root.addEventListener("input", (event) => {
    // A checkbox emits input before change. Do not reset its new checked state
    // before the change handler records the maintainer's review.
    if (event.target.id === "mlReviewed") return;
    if (event.target.id === "mlRepo") {
      state.reviewedRevision = null;
      renderCapabilities();
      renderMatches();
    }
    updateControls();
  });
  root.addEventListener("change", (event) => {
    if (event.target.id === "mlReviewed") state.reviewedRevision = event.target.checked ? repoKey() : null;
    if (event.target.id === "mlIncludeSuperseded") {
      state.includeSuperseded = event.target.checked;
      renderMatches();
    }
    updateControls();
  });
  root.addEventListener("click", async (event) => {
    const filter = event.target.closest("[data-ml-filter]");
    if (filter) {
      state.filter = filter.dataset.mlFilter;
      renderMatches();
      return;
    }
    const action = event.target.closest("[data-ml-action]");
    if (!action) return;
    if (action.dataset.mlAction === "refresh") return refresh();
    if (action.dataset.mlAction === "analyze") {
      try {
        const body = jobInput("analyze");
        if (body) await post("/api/missing-link/jobs", body, "Repository analysis queued. Source collection stays within this job's budget.");
      } catch (error) { note(error.message, true); }
    } else if (["cancel", "resume"].includes(action.dataset.mlAction)) {
      const body = { job_id: action.dataset.jobId };
      if (action.dataset.mlAction === "resume") {
        if (!find("mlMaxRequests").reportValidity()) return;
        const job = array(state.data?.jobs).find((item) => item.id === action.dataset.jobId);
        const newLimit = Number(find("mlMaxRequests").value);
        if (newLimit > Number(job?.input?.max_requests || 80)) body.max_requests = newLimit;
      }
      await post(`/api/missing-link/${action.dataset.mlAction}`, body, action.dataset.mlAction === "cancel" ? "Cancellation requested; the current bounded request may finish first." : "Resume requested within the explicitly selected total job budget.");
    }
  });
  root.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    if (form.id === "mlStartForm") {
      try {
        const body = jobInput("discover");
        if (body) await post("/api/missing-link/jobs", body, body.issue_url ? "Request evaluation queued." : "Capability-derived discovery queued. Coverage and incompleteness will remain visible.");
      } catch (error) { note(error.message, true); }
    } else if (form.classList.contains("ml-correction-form")) {
      const values = new FormData(form);
      const lines = (key) => String(values.get(key) || "").split("\n").map((value) => value.trim()).filter(Boolean);
      const correction = {
        name: values.get("name"), summary: values.get("summary"), outcome: values.get("outcome"),
        search_terms: lines("search_terms"), preconditions: lines("preconditions"), limitations: lines("limitations"),
        standalone: values.get("standalone"),
      };
      state.reviewedRevision = null;
      await post("/api/missing-link/capability", { repo: selectedRepo(), capability_id: form.dataset.capabilityId, correction }, "Maintainer correction saved separately from original source evidence. Review the updated capabilities again.");
    } else if (form.classList.contains("ml-feedback-form")) {
      const values = new FormData(form);
      await post("/api/missing-link/feedback", { match_id: form.dataset.matchId, decision: values.get("decision"), note: values.get("note") }, "Maintainer feedback saved without changing source evidence.");
    } else if (form.id === "mlImportForm") {
      const file = find("mlImportFile").files?.[0];
      const jobId = find("mlImportJob").value;
      if (!file || !jobId) return note("Choose the source job and a reviewed analysis JSON file.", true);
      if (file.size > 480000) return note("Analysis JSON must be at most 480 KB (the local API limit is 512 KB including its envelope).", true);
      try {
        const parsed = JSON.parse(await file.text());
        const analysis = parsed.analysis || parsed;
        await post("/api/missing-link/analysis", { job_id: jobId, analysis }, "Coding-agent analysis submitted. Source references are validated; no execution result is certified.");
      } catch (error) { note(`Could not import analysis: ${error.message}`, true); }
    }
  });

  updateRepositoryChoices();
  return {
    setActive(active) {
      const changed = state.active !== active;
      state.active = active;
      if (!active) { clearTimeout(state.timer); state.timer = null; }
      else if (changed || !state.data) refresh();
    },
    updateDashboard(dashboard) {
      const account = dashboard?.profile?.login;
      if (account && state.account && account.toLowerCase() !== state.account.toLowerCase()) {
        clearAccountState();
        state.account = null;
        render();
        note("GitHub account changed. Previous account results have been cleared; reload this account's Missing Link data.");
        if (state.active) refresh();
      } else updateRepositoryChoices();
    },
  };
}
