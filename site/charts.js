"use strict";
const chartEscape = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const CHART_DEPTH_LABELS = {
  "screened-structural": "Structural source screen",
  "abstract-only": "Abstract-level screen",
  "prior-screened-candidate": "Earlier screened candidate, not promoted"
};
let chartData;
let currentCounts;
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
// Read-only search over the entries of one edition. Order and positions are untouched.
function filterChartEntries(entries, query, topicLabel = id => id) {
  const needle = String(query || "").trim().toLowerCase();
  return entries.filter(row => JSON.stringify([row.title, row.claims, row.claims.map(id => topicLabel(id)), row.reason, row.family]).toLowerCase().includes(needle));
}
function chartFocus(row) {
  return EvidenceTopics.text(String(row.reason ?? "").split(";")[0]).replace(/^Relevant to /, "Focus: ");
}
function chartItem(kind, row) {
  const detail = `detail.html?type=${chartKindPath(kind)}&id=${encodeURIComponent(row.id)}`;
  return `<li><span class="chart-position" aria-label="Position ${row.position}">${row.position}</span><div><h2><a href="${chartEscape(detail)}">${chartEscape(row.title)}</a></h2><p class="badges"><span class="evidence-badge">${chartEscape(chartDepthLabel(kind, row))}</span>${row.record_state === "candidate-not-promoted" ? '<span class="evidence-badge">Candidate, not promoted</span>' : ""}</p><p>${chartEscape(chartFocus(row))}</p>${row.source_link_correction ? `<p class="note">Source link corrected ${chartEscape(row.source_link_correction.recorded_date)}. <a href="${chartEscape(row.source_link_correction.evidence_url)}">See the source evidence</a>.</p>` : ""}<p class="note">${row.claims.map(id => `<a href="claims.html#${id.toLowerCase()}">${chartEscape(EvidenceTopics.label(id))}</a>`).join(" · ")}${row.claims.length ? " · " : ""}Review priority ${row.priority_group} (tied entries share a number)</p><p class="card-actions"><a href="${chartEscape(detail)}">View profile</a> <a class="button secondary" href="${chartEscape(row.url)}">Open original source</a></p><details class="reference"><summary>Reference details</summary><p>Record ID: <code>${chartEscape(row.id)}</code></p><p>Evidence depth code: <code>${chartEscape(row.evidence_depth)}</code></p><p>Family code: <code>${chartEscape(row.family)}</code></p><p>Priority group: ${chartEscape(row.priority_group)}</p><p>Recorded reason: ${chartEscape(EvidenceTopics.text(row.reason))}</p>${row.snapshot_commit ? `<p>Source commit: <code>${chartEscape(row.snapshot_commit)}</code></p>` : ""}</details></div><aside><span class="movement">${chartEscape(chartMovement(row))}</span><span>Previous: ${row.previous_position ?? (row.entry_state === "reentry" ? "Off chart" : "First appearance")}</span><span>Peak: ${row.peak_position}</span><span>Appearances: ${row.appearances}</span></aside></li>`;
}
function renderChart() {
  const kind = document.querySelector("#chart-kind").value;
  const edition = chartData.history.find(row => row.edition_date === document.querySelector("#edition").value);
  const chart = edition.charts[kind];
  const query = document.querySelector("#chart-search").value;
  const rows = filterChartEntries(chart.entries, query, id => EvidenceTopics.label(id));
  document.querySelector("#chart-summary").textContent = `${rows.length} of ${chart.entries.length} chart entries shown. Current collection: ${currentCounts[kind]} source records. Edition ${edition.edition_date} preserves its original archive of ${chart.archive_count} records.`;
  document.querySelector("#chart-boundary").textContent = `${chart.eligible_count} records were eligible for this dated edition. New automated relevance checks await appraisal and are not automatically selected. ${chart.cutoff_tied_outside_chart ? `${chart.cutoff_tied_outside_chart} records share the cutoff priority but are outside this 100-position edition. ` : ""}A place on the chart grants no adoption authority. The edition date marks an editorial reevaluation of recorded evidence, not a freshness check on each source.`;
  document.querySelector("#chart-reset").disabled = !query.trim();
  document.querySelector("#chart-empty").hidden = rows.length > 0;
  document.querySelector("#chart-list").innerHTML = rows.map(row => chartItem(kind, row)).join("");
}
function resetChartSearch() {
  const search = document.querySelector("#chart-search");
  search.value = "";
  renderChart();
  search.focus();
}
async function loadCharts() {
  try {
    const response = await fetch("data/charts.json");
    if (!response.ok) throw new Error("Chart data is unavailable.");
    const claimsResponse = await fetch("data/claims.json");
    if (!claimsResponse.ok) throw new Error("Topic labels are unavailable.");
    EvidenceTopics.install(await claimsResponse.json());
    chartData = await response.json();
    const catalogs = await Promise.all(["research", "repositories"].map(async name => {
      const result = await fetch(`data/${name}.json`);
      if (!result.ok) throw new Error("Current collection counts are unavailable.");
      return [name, (await result.json()).length];
    }));
    currentCounts = Object.fromEntries(catalogs);
    document.querySelector("#edition").innerHTML = chartData.history.slice().reverse().map(row => `<option value="${chartEscape(row.edition_date)}">${chartEscape(row.edition_date)}</option>`).join("");
    for (const selector of ["#chart-kind", "#edition", "#chart-search"]) document.querySelector(selector).addEventListener(selector === "#chart-search" ? "input" : "change", renderChart);
    document.querySelector("#chart-reset").addEventListener("click", resetChartSearch);
    document.querySelector("#chart-empty-reset").addEventListener("click", resetChartSearch);
    renderChart();
  } catch (error) {
    const target = document.querySelector("#chart-error"); target.hidden = false; target.textContent = error.message;
    document.querySelector("#chart-summary").textContent = "The chart could not be loaded. Try again later or read the source ledger.";
  }
}
if (typeof document !== "undefined" && document.querySelector("#chart-list")) loadCharts();
