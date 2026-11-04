const type = document.body.dataset.catalog;
const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
}[char]));
const APPRAISAL_STATES = ["automated-screen", "source-screened"];
let items = [];
let claimsById = {};
let page = 1;
let tableView = false;

const $ = selector => document.querySelector(selector);
const label = CatalogUI.titleCase;
const isAutomated = CatalogUI.isAutomated;
const detailLink = (kind, id, text) =>
  `<a href="detail.html?type=${kind}&id=${encodeURIComponent(id)}">${escapeHtml(text)}</a>`;
const claimLinks = claims => claims.map(claim => `<a class="pill" href="claims.html#${claim.toLowerCase()}">${escapeHtml(EvidenceTopics.label(claim))}</a>`).join("");
const fact = (name, value, note = "") => `<div><dt>${escapeHtml(name)}</dt><dd>${value}${note ? `<small>${escapeHtml(note)}</small>` : ""}</dd></div>`;

function researchCard(item) {
  const automated = isAutomated(item);
  const depth = CatalogUI.researchDepth(item);
  const directness = CatalogUI.directnessText(item);
  const order = automated ? "Not ranked, awaiting appraisal" : `${item.evidenceOrder} of ${item.evidenceOrderCount}`;
  return `<article class="record-card">
    <p class="badges"><span class="pill depth">${escapeHtml(depth.label)}</span>${item.record_state === "candidate-not-promoted" ? '<span class="pill">Candidate, not promoted</span>' : ""}</p>
    <h3>${detailLink("research", item.id, item.title)}</h3>
    <p class="finding">${escapeHtml(EvidenceTopics.text(item.finding))}</p>
    <dl class="facts">
      ${fact("Directness", escapeHtml(directness.short), directness.note)}
      ${fact("Time span", escapeHtml(CatalogUI.horizonText(item)))}
      ${fact("Evidence family", escapeHtml(item.familyLabel))}
      ${fact("Recorded order", escapeHtml(order), "Sorted by directness, then time span. Not a quality score.")}
      ${fact("Publication or review date", "Not recorded", "Check the original source for its date.")}
    </dl>
    ${item.claims.length ? `<p class="topics"><span class="topics-label">Topics</span> ${claimLinks(item.claims)}</p>` : ""}
    <p class="card-actions">${detailLink("research", item.id, "View profile")} <a class="button secondary" href="${escapeHtml(item.url)}">Open original source</a></p>
    <details class="reference"><summary>Reference details</summary>
      <p>${escapeHtml(depth.note)}</p>
      <p>Review number: <code>${escapeHtml(item.id)}</code></p>
      <p>Family code: <code>${escapeHtml(item.family)}</code></p>
      <p>Review depth: <code>${escapeHtml(item.review_depth)}</code></p>
      <p>Citation signal: ${escapeHtml(item.citationSignal)}</p>
    </details>
  </article>`;
}

function repositoryCard(item) {
  const automated = isAutomated(item);
  const depth = CatalogUI.repositoryDepth(item);
  const stars = item.stars_observed === null || item.stars_observed === undefined ? "Not collected" : `${Number(item.stars_observed).toLocaleString()} stars`;
  const starsNote = item.stars_observed === null || item.stars_observed === undefined ? "" : `Observed ${CatalogUI.dateOrNotRecorded(item.starsObservedDate)}. Popularity only, not quality.`;
  const mechanisms = automated
    ? `All ${item.mechanismTotal} unknown`
    : `${item.visibleMechanisms} visible, ${item.partialMechanisms} partial, ${item.unknownMechanisms} unknown, of ${item.mechanismTotal}`;
  return `<article class="record-card">
    <p class="badges"><span class="pill depth">${escapeHtml(depth.label)}</span>${automated ? '<span class="pill">Unvetted third-party repository</span>' : ""}</p>
    <h3>${detailLink("repositories", item.id, item.repository)}</h3>
    <p class="finding">${escapeHtml(EvidenceTopics.text(item.evidence_note))}</p>
    <dl class="facts">
      ${fact("Category", escapeHtml(label(item.category)))}
      ${fact("Stars", escapeHtml(stars), starsNote)}
      ${fact("Mechanisms", escapeHtml(mechanisms), automated ? "Not appraised. Awaiting human review." : "Recorded from the evidence listed under reference details.")}
      ${fact("Source snapshot", escapeHtml(CatalogUI.dateOrNotRecorded(item.snapshot_date)), "The date the repository state was captured.")}
      ${fact(automated ? "Screen recorded" : "Review recorded", escapeHtml(CatalogUI.dateOrNotRecorded(item.lastReviewed)), "A metadata or README screen is not a full appraisal.")}
    </dl>
    ${item.claims.length ? `<p class="topics"><span class="topics-label">Topics</span> ${claimLinks(item.claims)}</p>` : ""}
    <p class="card-actions">${detailLink("repositories", item.id, "View profile")} <a class="button secondary" href="${escapeHtml(item.url)}">${automated ? "Open GitHub repository (unvetted)" : "Open GitHub repository"}</a></p>
    <details class="reference"><summary>Reference details</summary>
      <p>${escapeHtml(depth.note)}</p>
      <p>Record ID: <code>${escapeHtml(item.id)}</code></p>
      <p>Snapshot commit: <code>${escapeHtml(item.snapshot_commit ?? "not recorded")}</code></p>
      <p>Evidence depth: <code>${escapeHtml(item.evidence_depth)}</code></p>
      <p>Evidence pointer: <code>${escapeHtml(item.evidence_pointer ?? "not recorded")}</code></p>
    </details>
  </article>`;
}

function researchRow(item) {
  const automated = isAutomated(item);
  const directness = CatalogUI.directnessText(item);
  return `<tr>
    <td class="rank">${escapeHtml(item.id)}</td>
    <td class="rank">${automated ? "Unranked<br><small>(awaiting appraisal)</small>" : `${item.evidenceOrder}<small> / ${item.evidenceOrderCount}</small>`}</td>
    <td><strong>${detailLink("research", item.id, item.title)}</strong>${item.record_state === "candidate-not-promoted" ? '<br><span class="pill">Candidate, not promoted</span>' : ""}<br><span class="pill">${escapeHtml(CatalogUI.researchDepth(item).label)}</span><br><a href="${escapeHtml(item.url)}">Original source</a></td>
    <td><strong>${automated ? "Not appraised" : `${item.directnessValue} / 3`}</strong>${automated ? "" : `<br><span class="pill">${escapeHtml(directness.short)}</span>`}</td>
    <td><strong>${automated ? "Not appraised" : `${item.horizonValue} / 3`}</strong>${automated ? "" : `<br><span class="pill">${escapeHtml(CatalogUI.horizonText(item))}</span>`}</td>
    <td><strong>${item.claimCount}</strong><br>${claimLinks(item.claims)}</td>
    <td>${escapeHtml(item.citationSignal)}</td>
    <td>${escapeHtml(EvidenceTopics.text(item.finding))}</td>
    <td>${escapeHtml(EvidenceTopics.text(item.impact))}</td>
    <td>${escapeHtml(EvidenceTopics.text(item.flags))}</td>
  </tr>`;
}

function repositoryRow(item) {
  const popularity = item.popularityOrder ? `${item.popularityOrder}<small> / ${item.popularityCount}</small>` : "Not collected";
  const categoryRank = item.categoryPopularityOrder ? `${item.categoryPopularityOrder} / ${item.categoryPopularityCount}` : "Not collected";
  const stars = item.stars_observed === null ? "Not collected" : `<strong>${Number(item.stars_observed).toLocaleString()}</strong><br><small>observed ${escapeHtml(item.starsObservedDate)}</small>`;
  const automated = isAutomated(item);
  return `<tr>
    <td class="rank">${popularity}</td>
    <td><strong>${detailLink("repositories", item.id, item.repository)}</strong>${automated ? '<br><span class="pill">Unvetted third-party repository</span>' : ""}<br><a href="${escapeHtml(item.url)}">GitHub repository</a></td>
    <td><strong>${categoryRank}</strong></td>
    <td><span class="pill">${escapeHtml(label(item.category))}</span></td>
    <td>${escapeHtml(label(item.selection_aspect))}</td>
    <td>${stars}</td>
    <td><strong>${item.visibleMechanisms} / ${item.mechanismTotal}</strong> visible<br><strong>${item.partialMechanisms} / ${item.mechanismTotal}</strong> partial<br><strong>${item.unknownMechanisms} / ${item.mechanismTotal}</strong> unknown</td>
    <td><strong>${item.claimCount}</strong><br>${claimLinks(item.claims)}</td>
    <td><strong>${automated ? "Screen recorded" : "Review recorded"} ${escapeHtml(item.lastReviewed)}</strong><br><span class="pill">${escapeHtml(CatalogUI.repositoryDepth(item).label)}</span></td>
    <td>${escapeHtml(EvidenceTopics.text(item.evidence_note))}</td>
  </tr>`;
}

const selectedText = selector => {
  const control = $(selector);
  return control.options[control.selectedIndex].text;
};
const currentState = () => ({
  query: $("#search").value, filter: $("#filter").value, theme: $("#theme").value,
  claim: $("#claim").value, depth: $("#depth").value, sort: $("#sort").value
});

function render() {
  const state = currentState();
  const matches = CatalogUI.sortItems(CatalogUI.filterItems(type, items, state, id => EvidenceTopics.label(id)), state.sort);
  const range = CatalogUI.paginate(matches.length, page, Number($("#page-size").value));
  page = range.page;
  const visible = matches.slice(range.start ? range.start - 1 : 0, range.end);
  $("#cards").innerHTML = visible.map(type === "research" ? researchCard : repositoryCard).join("");
  $("tbody").innerHTML = visible.map(type === "research" ? researchRow : repositoryRow).join("");
  $("#count").textContent = CatalogUI.countText(items.length, matches.length, range, type === "research" ? "research records" : "repositories");
  const active = CatalogUI.activeFilters([
    {name: "Search", value: state.query.trim(), text: `"${state.query.trim()}"`},
    {name: type === "research" ? "Directness" : "Category", value: state.filter, text: state.filter ? selectedText("#filter") : ""},
    {name: type === "research" ? "Evidence family" : "Repository status", value: state.theme, text: state.theme ? selectedText("#theme") : ""},
    {name: "Topic", value: state.claim, text: state.claim ? selectedText("#claim") : ""},
    {name: "Evidence depth", value: state.depth, text: state.depth ? selectedText("#depth") : ""}
  ]);
  $("#filter-summary").textContent = CatalogUI.filterSummaryText(active);
  $("#reset").disabled = active.length === 0 && state.sort === "rank";
  $("#empty").hidden = matches.length > 0;
  $("#pager").hidden = matches.length === 0;
  $("#prev").disabled = !range.hasPrev;
  $("#next").disabled = !range.hasNext;
  $("#page-status").textContent = `Page ${range.page} of ${range.pages}`;
  $("#cards").hidden = tableView || matches.length === 0;
  $("#table-view").hidden = !tableView || matches.length === 0;
}

function addOptions(control, pairs) {
  control.innerHTML += pairs.map(([value, text]) => `<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`).join("");
}

function depthOptionText(value) {
  if (type === "research") {
    return value === "abstract-only"
      ? "Abstract only (includes relevance checks awaiting appraisal)"
      : CatalogUI.researchDepth({review_depth: value}).label;
  }
  return CatalogUI.repositoryDepth({evidence_depth: value}).label;
}

function resetFilters() {
  for (const selector of ["#search", "#filter", "#theme", "#claim", "#depth"]) $(selector).value = "";
  $("#sort").value = "rank";
  page = 1;
  render();
  $("#search").focus();
}

function goToPage(delta) {
  page += delta;
  render();
  $("#results").focus({preventScroll: true});
  $("#results").scrollIntoView({block: "start"});
}

function setView(table) {
  tableView = table;
  $("#view-toggle").textContent = table ? "Show cards" : "Show comparison table";
  $("#view-toggle").setAttribute("aria-pressed", String(table));
  render();
}

async function catalog() {
  if (!type) return;
  const response = await fetch(`data/${type}.json`);
  if (!response.ok) throw new Error("Catalog data unavailable");
  items = await response.json();
  if (items.some(item => !APPRAISAL_STATES.includes(item.appraisal_state))) throw new Error("Unknown appraisal state");
  if (type === "research") {
    $(".catalog-head .eyebrow").textContent = `Research · ${items.length} records`;
    const automated = items.filter(isAutomated).length;
    $(".catalog-head .lede").textContent =
      `${items.length - automated} records carry a recorded source screen, grade and order. ${automated} are abstract relevance checks awaiting appraisal: they have no directness or horizon grade and are listed after the others. A screen finds material to read. It does not validate a finding, and no record here is treated as fully appraised unless its profile says so.`;
  } else {
    const detailed = items.filter(item => item.evidence_depth === "readme-screened").length;
    const portable = items.filter(item => item.evidence_depth === "source-assessment").length;
    const relevance = items.filter(item => item.evidence_depth === "readme-relevance-screened").length;
    if (detailed + portable + relevance !== items.length) throw new Error("Unknown repository evidence depth");
    $(".catalog-head .eyebrow").textContent = `Repositories · ${items.length} records`;
    $(".catalog-head .lede").textContent =
      `${detailed} were README screened against a pinned revision, ${portable} are portable records (identity and provenance only), and ${relevance} are README relevance checks awaiting appraisal and are unvetted third-party repositories. Mechanisms stay unknown until a human appraises them. Stars are popularity only and do not establish quality.`;
  }
  const claims = await fetch("data/claims.json").then(result => result.json());
  EvidenceTopics.install(claims);
  claimsById = Object.fromEntries(claims.map(item => [item.id, item]));
  if (type === "research") {
    addOptions($("#filter"), ["D3", "D2", "D1", "D0"].map(key => [key, CatalogUI.DIRECTNESS[key].name]));
    if (items.some(isAutomated)) addOptions($("#filter"), [[CatalogUI.UNAPPRAISED, "Awaiting appraisal (no grade yet)"]]);
    const families = new Map(items.map(item => [item.family, item.familyLabel]));
    addOptions($("#theme"), [...families].sort((a, b) => a[1].localeCompare(b[1])));
  } else {
    addOptions($("#filter"), [...new Set(items.map(item => item.category))].sort().map(value => [value, label(value)]));
    addOptions($("#theme"), [...new Set(items.map(item => item.lifecycle))].sort().map(value => [value, label(value)]));
  }
  addOptions($("#claim"), [...new Set(items.flatMap(item => item.claims))].sort().map(value => [value, EvidenceTopics.label(value)]));
  addOptions($("#depth"), [...new Set(items.map(item => CatalogUI.depthValue(type, item)))].sort().map(value => [value, depthOptionText(value)]));
  for (const selector of ["#search", "#filter", "#theme", "#claim", "#depth", "#sort", "#page-size"]) {
    $(selector).addEventListener(selector === "#search" ? "input" : "change", () => { page = 1; render(); });
  }
  $("#reset").addEventListener("click", resetFilters);
  $("#empty-reset").addEventListener("click", resetFilters);
  $("#prev").addEventListener("click", () => goToPage(-1));
  $("#next").addEventListener("click", () => goToPage(1));
  $("#view-toggle").addEventListener("click", () => setView(!tableView));
  render();
}

catalog().catch(() => {
  $("#count").textContent = "The catalog could not load.";
  $("#load-error").hidden = false;
  $("#empty").hidden = true;
  for (const control of document.querySelectorAll(".catalog-controls input, .catalog-controls select, .catalog-controls button")) control.disabled = true;
});
