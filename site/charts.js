"use strict";
const chartEscape = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const safeChartHttps = value => {
  const raw = String(value ?? "").trim();
  return /^https:\/\/[^\s"'<>]+$/i.test(raw) ? raw : "";
};
const CHART_DEPTH_LABELS = {
  "selected-full-text": "Selected full-text review",
  "screened-structural": "Structural source screen",
  "abstract-only": "Abstract-level screen",
  "prior-screened-candidate": "Earlier screened candidate, not promoted"
};
let chartData;
let currentCoverage;
const chartKindPath = kind => kind === "research" ? "research" : "repositories";
function chartDepthLabel(kind, row) {
  if (kind === "research") return CHART_DEPTH_LABELS[row.evidence_depth] || CatalogUI.titleCase(row.evidence_depth);
  return CatalogUI.repositoryDepth({evidence_depth: row.evidence_depth}).label;
}
function chartMovement(row) {
  if (row.entry_state === "new") return "NEW";
  if (row.entry_state === "reentry") return "RE-ENTRY";
  if (row.movement > 0) return `UP ${row.movement}`;
  if (row.movement < 0) return `DOWN ${-row.movement}`;
  return "UNCHANGED";
}
function chartMovementClass(row) {
  if (row.entry_state === "new" || row.entry_state === "reentry") return "movement is-new";
  if (row.movement > 0) return "movement is-up";
  if (row.movement < 0) return "movement is-down";
  return "movement";
}
// Read-only filter over the entries of one edition. Order and positions are untouched.
function filterChartEntries(entries, query, topicLabel = id => id, filters = {}) {
  const needle = String(query || "").trim().toLowerCase();
  const claim = String(filters.claim || "").trim();
  const depth = String(filters.depth || "").trim();
  return entries.filter(row => {
    if (claim && !(row.claims || []).includes(claim)) return false;
    if (depth && row.evidence_depth !== depth) return false;
    if (!needle) return true;
    return JSON.stringify([row.title, row.claims, (row.claims || []).map(id => topicLabel(id)), row.reason, row.family, row.category || ""]).toLowerCase().includes(needle);
  });
}
function chartFocus(row) {
  return EvidenceTopics.text(String(row.reason ?? "").split(";")[0]).replace(/^Relevant to /, "Focus: ");
}
function chartMetaContext(kind, row) {
  if (kind === "research") {
    const parts = [];
    if (row.directness) parts.push(CatalogUI.directnessText(row).short);
    if (row.horizon) parts.push(CatalogUI.horizonText(row));
    return parts.length ? ` · ${parts.join(" · ")}` : "";
  }
  const parts = [];
  if (row.category) parts.push(CatalogUI.titleCase(row.category));
  if (row.stars_observed !== null && row.stars_observed !== undefined) {
    parts.push(`${Number(row.stars_observed).toLocaleString()} stars observed`);
  }
  return parts.length ? ` · ${parts.join(" · ")}` : "";
}
function chartItem(kind, row) {
  const detail = `detail.html?type=${chartKindPath(kind)}&id=${encodeURIComponent(row.id)}`;
  const sourceHref = safeChartHttps(row.url);
  const sourceAction = sourceHref ? ` <a class="button secondary" href="${chartEscape(sourceHref)}">Open original source</a>` : "";
  const topicPills = (row.claims || []).map(id => `<a class="pill" href="claims.html#${encodeURIComponent(String(id).toLowerCase())}">${chartEscape(EvidenceTopics.label(id))}</a>`).join("");
  const correctionHref = row.source_link_correction ? safeChartHttps(row.source_link_correction.evidence_url) : "";
  const correctionNote = row.source_link_correction
    ? `<p class="note">Source link corrected ${chartEscape(row.source_link_correction.recorded_date)}.${correctionHref ? ` <a href="${chartEscape(correctionHref)}">See the source evidence</a>.` : ""}</p>`
    : "";
  const prevText = row.previous_position !== null && row.previous_position !== undefined
    ? chartEscape(row.previous_position)
    : (row.entry_state === "reentry" ? "Off chart" : "First appearance");
  return `<li><span class="chart-position" aria-label="Position ${chartEscape(row.position)}">${chartEscape(row.position)}</span><div><h2><a href="${chartEscape(detail)}">${chartEscape(row.title)}</a></h2><p class="badges"><span class="evidence-badge">${chartEscape(chartDepthLabel(kind, row))}</span>${row.record_state === "candidate-not-promoted" ? '<span class="evidence-badge">Candidate, not promoted</span>' : ""}</p><p class="chart-focus">${chartEscape(chartFocus(row))}</p>${correctionNote}${topicPills ? `<p class="topics"><span class="topics-label">Topics</span> ${topicPills}</p>` : ""}<p class="chart-priority">Review priority ${chartEscape(row.priority_group)} (tied entries share a number)${chartEscape(chartMetaContext(kind, row))}</p><p class="card-actions"><a href="${chartEscape(detail)}">View profile</a>${sourceAction}</p><details class="reference"><summary>Reference details</summary><p>Record ID: <code>${chartEscape(row.id)}</code></p><p>Evidence depth code: <code>${chartEscape(row.evidence_depth)}</code></p><p>Family code: <code>${chartEscape(row.family)}</code></p><p>Priority group: ${chartEscape(row.priority_group)}</p><p>Recorded reason: ${chartEscape(EvidenceTopics.text(row.reason))}</p>${row.snapshot_commit ? `<p>Source commit: <code>${chartEscape(row.snapshot_commit)}</code></p>` : ""}</details></div><aside><span class="${chartMovementClass(row)}">${chartEscape(chartMovement(row))}</span><span>Previous: ${prevText}</span><span>Peak: ${chartEscape(row.peak_position)}</span><span>Appearances: ${chartEscape(row.appearances)}</span></aside></li>`;
}
function syncChartSelectOptions(kind, entries) {
  const claimEl = document.querySelector("#chart-claim");
  const depthEl = document.querySelector("#chart-depth");
  const prevClaim = claimEl.value;
  const prevDepth = depthEl.value;
  const claimSet = new Set(entries.flatMap(row => row.claims || []));
  const depthSet = new Set(entries.map(row => row.evidence_depth).filter(Boolean));
  claimEl.innerHTML = `<option value="">All topics</option>` + [...claimSet].sort().map(id => `<option value="${chartEscape(id)}">${chartEscape(EvidenceTopics.label(id))}</option>`).join("");
  depthEl.innerHTML = `<option value="">Any depth</option>` + [...depthSet].sort().map(d => `<option value="${chartEscape(d)}">${chartEscape(chartDepthLabel(kind, {evidence_depth: d}))}</option>`).join("");
  claimEl.value = claimSet.has(prevClaim) ? prevClaim : "";
  depthEl.value = depthSet.has(prevDepth) ? prevDepth : "";
}
function hasChartOption(control, candidate) {
  if (!candidate || !control) return false;
  return Array.from(control.options || []).some(opt => opt.value === candidate);
}
function applyChartLocationFilters() {
  if (typeof location === "undefined" || !location.search) return;
  const params = new URLSearchParams(location.search);
  const kindParam = (params.get("kind") || "").trim();
  if (hasChartOption(document.querySelector("#chart-kind"), kindParam)) {
    document.querySelector("#chart-kind").value = kindParam;
  }
  const editionParam = (params.get("edition") || "").trim();
  if (hasChartOption(document.querySelector("#edition"), editionParam)) {
    document.querySelector("#edition").value = editionParam;
  }
  const kind = document.querySelector("#chart-kind").value;
  const edition = chartData.history.find(row => row.edition_date === document.querySelector("#edition").value) || chartData.latest;
  syncChartSelectOptions(kind, edition.charts[kind].entries);
  const claimParam = (params.get("claim") || "").trim().toUpperCase();
  if (hasChartOption(document.querySelector("#chart-claim"), claimParam)) {
    document.querySelector("#chart-claim").value = claimParam;
  }
  const depthParam = (params.get("depth") || "").trim();
  if (hasChartOption(document.querySelector("#chart-depth"), depthParam)) {
    document.querySelector("#chart-depth").value = depthParam;
  }
  const query = (params.get("q") || params.get("query") || "").trim();
  if (query) document.querySelector("#chart-search").value = query.slice(0, 200);
}
function syncChartLocation() {
  if (typeof history === "undefined" || typeof history.replaceState !== "function" || typeof location === "undefined") return;
  const params = new URLSearchParams();
  const kind = document.querySelector("#chart-kind").value;
  const edition = document.querySelector("#edition").value;
  const claim = document.querySelector("#chart-claim").value;
  const depth = document.querySelector("#chart-depth").value;
  const query = document.querySelector("#chart-search").value.trim();
  if (kind && kind !== "research") params.set("kind", kind);
  if (edition && chartData && edition !== chartData.latest.edition_date) params.set("edition", edition);
  if (claim) params.set("claim", claim);
  if (depth) params.set("depth", depth);
  if (query) params.set("q", query);
  const qs = params.toString();
  const base = location.pathname || "charts.html";
  history.replaceState(null, "", `${base}${qs ? `?${qs}` : ""}${location.hash || ""}`);
}
function renderChart(refreshOptions = false) {
  const kind = document.querySelector("#chart-kind").value;
  const edition = chartData.history.find(row => row.edition_date === document.querySelector("#edition").value) || chartData.latest;
  const chart = edition.charts[kind];
  if (refreshOptions) syncChartSelectOptions(kind, chart.entries);
  const query = document.querySelector("#chart-search").value;
  const claim = document.querySelector("#chart-claim").value;
  const depth = document.querySelector("#chart-depth").value;
  const rows = filterChartEntries(chart.entries, query, id => EvidenceTopics.label(id), {claim, depth});
  const {total, screened, awaiting} = currentCoverage[kind];
  const current = document.querySelector("#current-collection");
  current.textContent = `Current collection: ${total} records. ${screened} source-screened. ${awaiting} await appraisal after automated screening.`;
  current.href = `${chartKindPath(kind)}.html`;
  current.hidden = false;
  document.querySelector("#chart-summary").textContent = `${rows.length} of ${chart.entries.length} chart entries shown.`;
  const latest = chartData.latest.edition_date;
  const editionLabel = edition.edition_date === latest ? "Latest edition" : "Historical edition";
  const latestNote = edition.edition_date === latest ? "" : ` Latest edition: ${latest}.`;
  document.querySelector("#chart-boundary").textContent = `${editionLabel} ${edition.edition_date}: ${chart.eligible_count} of ${chart.archive_count} records were eligible on that date.${latestNote} ${chart.cutoff_tied_outside_chart ? `${chart.cutoff_tied_outside_chart} records share the cutoff priority but are outside this 100-position edition. ` : ""}Source screening depth varies. The edition reflects an editorial review of recorded evidence.`;
  document.querySelector("#chart-reset").disabled = !query.trim() && !claim && !depth;
  document.querySelector("#chart-empty").hidden = rows.length > 0;
  document.querySelector("#chart-list").innerHTML = rows.map(row => chartItem(kind, row)).join("");
}
function resetChartSearch() {
  const search = document.querySelector("#chart-search");
  search.value = "";
  document.querySelector("#chart-claim").value = "";
  document.querySelector("#chart-depth").value = "";
  syncChartLocation();
  renderChart();
  search.focus();
}
async function loadCharts() {
  try {
    const response = await fetch("data/charts.json", {cache: "no-cache"});
    if (!response.ok) throw new Error("Chart data is unavailable.");
    const claimsResponse = await fetch("data/claims.json");
    if (!claimsResponse.ok) throw new Error("Topic labels are unavailable.");
    EvidenceTopics.install(await claimsResponse.json());
    chartData = await response.json();
    const catalogs = await Promise.all(["research", "repositories"].map(async name => {
      const result = await fetch(`data/${name}.json`, {cache: "no-cache"});
      if (!result.ok) throw new Error("Current collection counts are unavailable.");
      const records = await result.json();
      return [name, {
        total: records.length,
        screened: records.filter(row => row.appraisal_state === "source-screened").length,
        awaiting: records.filter(row => row.appraisal_state === "automated-screen").length
      }];
    }));
    currentCoverage = Object.fromEntries(catalogs);
    const edition = document.querySelector("#edition");
    const latest = chartData.latest.edition_date;
    edition.innerHTML = chartData.history.slice().reverse().map(row => `<option value="${chartEscape(row.edition_date)}">${chartEscape(row.edition_date)}${row.edition_date === latest ? " (latest)" : ""}</option>`).join("");
    edition.value = latest;
    syncChartSelectOptions("research", chartData.latest.charts.research.entries);
    applyChartLocationFilters();
    for (const selector of ["#chart-kind", "#edition"]) {
      document.querySelector(selector).addEventListener("change", () => { syncChartLocation(); renderChart(true); });
    }
    for (const selector of ["#chart-claim", "#chart-depth"]) {
      document.querySelector(selector).addEventListener("change", () => { syncChartLocation(); renderChart(false); });
    }
    document.querySelector("#chart-search").addEventListener("input", () => { syncChartLocation(); renderChart(false); });
    document.querySelector("#chart-reset").addEventListener("click", resetChartSearch);
    document.querySelector("#chart-empty-reset").addEventListener("click", resetChartSearch);
    renderChart(false);
  } catch (error) {
    const target = document.querySelector("#chart-error"); target.hidden = false; target.textContent = error.message;
    document.querySelector("#chart-summary").textContent = "The chart could not be loaded. Try again later or read the source ledger.";
  }
}
if (typeof document !== "undefined" && document.querySelector("#chart-list")) loadCharts();
