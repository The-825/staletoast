const esc = (value = "") => String(value ?? "").replace(/[&<>'"]/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[character]));
const params = new URLSearchParams(location.search);
const type = params.get("type");
const id = params.get("id");
const pills = values => values.map(value => `<span class="pill">${esc(value)}</span>`).join("");
const bar = (label, value, total, tone = "visible") => value === null || value === undefined ? `<p>${esc(label)}: not appraised</p>` : `<div class="bar-row"><span>${esc(label)}</span><div class="bar-track" aria-hidden="true"><i class="${tone}" style="width:${Math.round((value / total) * 100)}%"></i></div><strong>${value} / ${total}</strong></div>`;
const sentence = value => value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
const claimsOf = item => Array.isArray(item.claims) ? item.claims : [];
const relatedByClaims = (candidates, item, name) => candidates.filter(candidate => candidate.id !== item.id && claimsOf(candidate).some(claim => claimsOf(item).includes(claim))).map(candidate => ({candidate, overlap: claimsOf(candidate).filter(claim => claimsOf(item).includes(claim)).length})).sort((a, b) => b.overlap - a.overlap || name(a.candidate).localeCompare(name(b.candidate))).slice(0, 5).map(result => result.candidate);
const claimLinks = (values, claimsById) => values.map(value => `<a class="claim-link" href="claims.html#${value.toLowerCase()}"><strong>${esc(EvidenceTopics.label(value))}</strong></a>`).join("");
const relatedList = (records, kind, name, emptyText) => records.map(candidate => `<a href="detail.html?type=${kind}&id=${encodeURIComponent(candidate.id)}">${esc(name(candidate))}</a>`).join("") || `<p>${esc(emptyText)}</p>`;
const backLink = (href, text) => `<p class="back-link"><a href="${href}">&larr; ${esc(text)}</a></p>`;

function research(item, all, repositories, claimsById) {
  const related = relatedByClaims(all, item, candidate => candidate.title);
  const linked = relatedByClaims(repositories, item, candidate => candidate.repository);
  const automated = item.appraisal_state === "automated-screen";
  const depth = CatalogUI.researchDepth(item);
  const directness = CatalogUI.directnessText(item);
  const candidate = item.record_state === "candidate-not-promoted" ? `<p class="note">Candidate, not promoted. Review depth: ${esc(depth.label)}. Source screening is not a validated finding or adopted practice.</p>` : "";
  const intake = automated ? `<p class="note">This is an abstract relevance check awaiting appraisal. It has no evidence order, directness or horizon grade, and its text is not a validated finding.</p>` : "";
  return `${backLink("research.html", "Back to all research")}<p class="eyebrow">Research profile</p><h1>${esc(item.title)}</h1>${candidate}${intake}<p class="lede">${esc(EvidenceTopics.text(item.finding))}</p>
    <div class="profile"><div class="meter"><small>Evidence order</small><strong>${automated ? "Unranked" : `${item.evidenceOrder} / ${item.evidenceOrderCount}`}</strong>${automated ? "<span>awaiting appraisal</span>" : ""}</div><div class="meter"><small>Directness</small><strong>${automated || item.directnessValue === null ? "Not appraised" : `${item.directnessValue} / 3`}</strong><span>${esc(directness.short)}</span></div><div class="meter"><small>Horizon</small><strong>${automated || item.horizonValue === null ? "Not appraised" : `${item.horizonValue} / 3`}</strong><span>${esc(CatalogUI.horizonText(item))}</span></div><div class="meter"><small>Citation signal</small><strong>${esc(item.citationSignal)}</strong></div></div>
    <section class="detail split-detail"><div><p class="eyebrow">Our reading</p><h2>What this changes</h2><p>${esc(EvidenceTopics.text(sentence(item.impact)))}</p><h3>Boundary and next question</h3><p>${esc(EvidenceTopics.text(sentence(item.boundary)))}</p></div><div class="signal-panel"><h3>Evidence profile</h3>${bar("Directness", item.directnessValue, 3)}${bar("Horizon", item.horizonValue, 3, "partial")}<p><strong>Evidence depth:</strong> ${esc(depth.label)}. ${esc(depth.note)}</p><p><strong>What directness means here:</strong> ${esc(directness.note)}</p><p><strong>Evidence family:</strong> ${esc(item.familyLabel)}</p><p><strong>Study design:</strong> ${esc(sentence(item.design))}</p><p><strong>Publication or review date:</strong> not recorded. Open the original source to check its date.</p></div></section>
    <section class="section related"><div class="card"><h2>Visible risks</h2><p>${esc(EvidenceTopics.text(sentence(item.flags)))}</p><h3>Linked topics</h3><div class="claim-links">${claimLinks(claimsOf(item), claimsById) || "<p>No linked topics recorded.</p>"}</div></div><div class="card"><h2>What to do next</h2><p>Read the original source, compare its setting with your own, then decide whether the boundary above lets you apply it. The original source remains authoritative. This profile is a bounded interpretation.</p><p><a class="button" href="${esc(item.url)}">Open original source</a></p><p><a href="https://the-825.github.io/breadcrumbs/start.html">Try a small change with Breadcrumbs</a></p></div></section>
    <section class="section related"><div class="card"><h2>Related research</h2>${relatedList(related, "research", candidate => candidate.title, "No related research was found through shared topics.")}</div><div class="card"><h2>Related repositories</h2>${relatedList(linked, "repositories", candidate => candidate.repository, "No related repositories were found through shared topics.")}</div></section>
    <details class="reference"><summary>Reference details</summary><p>Review number: <code>${esc(item.id)}</code></p><p>Evidence family code: <code>${esc(item.family)}</code></p><p>Review depth code: <code>${esc(item.review_depth)}</code></p><p>Appraisal state: <code>${esc(item.appraisal_state)}</code></p><p>Record state: <code>${esc(item.record_state)}</code></p><p>Directness grade: <code>${esc(item.directness ?? "not graded")}</code></p><p>Horizon grade: <code>${esc(item.horizon ?? "not graded")}</code></p><p>Topic IDs: <code>${esc(claimsOf(item).join(", ") || "none")}</code></p><p>Evidence level as recorded: ${esc(item.levelEvidence)}</p></details>
    ${backLink("research.html", "Back to all research")}`;
}

function repository(item, all, researchItems, claimsById) {
  const related = relatedByClaims(all, item, candidate => candidate.repository);
  const linked = relatedByClaims(researchItems, item, candidate => candidate.title);
  const mechanisms = item.mechanisms && typeof item.mechanisms === "object" ? item.mechanisms : null;
  const names = code => mechanisms ? Object.entries(mechanisms).filter(([, value]) => value === code).map(([key]) => CatalogUI.mechanismName(key)) : [];
  const visible = names("V");
  const partial = names("P");
  const unknown = names("U");
  const notObserved = mechanisms ? item.mechanismTotal - visible.length - partial.length - unknown.length : null;
  const popularity = item.popularityOrder ? `${item.popularityOrder} / ${item.popularityCount}` : "Not collected";
  const categoryRank = item.categoryPopularityOrder ? `${item.categoryPopularityOrder} / ${item.categoryPopularityCount}` : "Not collected";
  const stars = item.stars_observed === null || item.stars_observed === undefined ? "Not collected" : Number(item.stars_observed).toLocaleString();
  const automated = item.appraisal_state === "automated-screen";
  const depth = CatalogUI.repositoryDepth(item);
  const intake = automated ? `<p class="note">This is a README relevance check awaiting appraisal. It is an unvetted third-party repository: no mechanism, license text or safety assessment was performed. GitHub-reported license metadata is unverified.</p>` : "";
  const profile = mechanisms
    ? `<h3>Mechanism profile</h3>${bar("Visible", visible.length, item.mechanismTotal)}${bar("Partial", partial.length, item.mechanismTotal, "partial")}${bar("Unknown", unknown.length, item.mechanismTotal, "quiet")}${bar("Not observed or out of scope", notObserved, item.mechanismTotal, "quiet")}<p><strong>Visible</strong> means the pinned evidence directly exposed the mechanism. <strong>Partial</strong> means only part of the mechanism was exposed or the evidence was incomplete. <strong>Unknown</strong> means the assessment did not establish the mechanism.</p><p class="note">This chart reports what the recorded evidence supports. It is not a performance score.</p>`
    : `<h3>Mechanism profile</h3><p>No mechanism profile is recorded for this repository.</p>`;
  const mechanismRows = mechanisms ? Object.entries(mechanisms).map(([key, value]) => `<li>${esc(CatalogUI.mechanismName(key))}: ${esc(CatalogUI.mechanismState(value))} (<code>${esc(key)}=${esc(value)}</code>)</li>`).join("") : "";
  return `${backLink("repositories.html", "Back to all repositories")}<p class="eyebrow">Repository profile</p><h1>${esc(item.repository)}</h1>${intake}<p class="lede">${esc(EvidenceTopics.text(item.evidence_note))}</p>
    <div class="profile"><div class="meter"><small>Stars position</small><strong>${popularity}</strong><span>popularity only</span></div><div class="meter"><small>Within category</small><strong>${categoryRank}</strong><span>${esc(CatalogUI.titleCase(item.category))}</span></div><div class="meter"><small>Stars observed</small><strong>${stars}</strong><span>${item.stars_observed === null || item.stars_observed === undefined ? "" : `on ${esc(CatalogUI.dateOrNotRecorded(item.starsObservedDate))}`}</span></div><div class="meter"><small>${automated ? "Screen recorded" : "Last reviewed"}</small><strong>${esc(CatalogUI.dateOrNotRecorded(item.lastReviewed))}</strong><span>${esc(depth.label)}</span></div></div>
    <section class="detail split-detail"><div><p class="eyebrow">Our reading</p><h2>What is visible</h2><p>${esc(EvidenceTopics.text(sentence(item.evidence_note)))}</p><h3>Evidence depth</h3><p><strong>${esc(depth.label)}.</strong> ${esc(depth.note)}</p><h3>Dates</h3><p><strong>Source snapshot:</strong> ${esc(CatalogUI.dateOrNotRecorded(item.snapshot_date))}<br><strong>${automated ? "Screen recorded" : "Review recorded"}:</strong> ${esc(CatalogUI.dateOrNotRecorded(item.lastReviewed))}<br><strong>Stars observed:</strong> ${esc(CatalogUI.dateOrNotRecorded(item.starsObservedDate))}</p><h3>Classification</h3><p><strong>Category:</strong> ${esc(CatalogUI.titleCase(item.category))}<br><strong>Selection lens:</strong> ${esc(CatalogUI.titleCase(item.selection_aspect))}</p><h3>Linked topics</h3><div class="claim-links">${claimLinks(claimsOf(item), claimsById) || "<p>No linked topics recorded.</p>"}</div></div><div class="signal-panel">${profile}</div></section>
    <section class="section related"><div class="card"><h2>Visible mechanisms</h2>${pills(visible) || "<p>None observed.</p>"}</div><div class="card"><h2>Partial mechanisms</h2>${pills(partial) || "<p>None observed.</p>"}</div></section>
    <section class="section related"><div class="card"><h2>Related repositories</h2>${relatedList(related, "repositories", candidate => candidate.repository, "No related repositories were found through shared topics.")}</div><div class="card"><h2>Related research</h2>${relatedList(linked, "research", candidate => candidate.title, "No related research was found through shared topics.")}</div></section>
    <section class="section"><div class="card"><h2>What to do next</h2><p>Open the repository and read it yourself before relying on it. Stars are a dated audience signal, popularity only, and can change as the collection grows. Evidence depth describes the review performed. Neither proves quality.</p><a class="button" href="${esc(item.url)}">${automated ? "Open GitHub repository (unvetted third party)" : "Open GitHub repository"}</a> <a class="button secondary" href="https://the-825.github.io/breadcrumbs/start.html">Try a small change with Breadcrumbs</a></div></section>
    <details class="reference"><summary>Reference details</summary><p>Record ID: <code>${esc(item.id)}</code></p><p>Snapshot commit: <code>${esc(item.snapshot_commit ?? "not recorded")}</code></p><p>Upstream revision: <code>${esc(item.upstream_revision ?? "not recorded")}</code></p><p>Evidence depth code: <code>${esc(item.evidence_depth)}</code></p><p>Evidence pointer: <code>${esc(item.evidence_pointer ?? "not recorded")}</code></p><p>Assessment status: <code>${esc(item.assessment_status ?? "not recorded")}</code></p><p>Appraisal state: <code>${esc(item.appraisal_state)}</code></p><p>License status as recorded: ${esc(item.license_status ?? "not recorded")}</p>${item.readme_content_sha256 ? `<p>README digest: <code>${esc(item.readme_content_sha256)}</code></p>` : ""}${mechanismRows ? `<p>Mechanism codes:</p><ul>${mechanismRows}</ul>` : ""}</details>
    ${backLink("repositories.html", "Back to all repositories")}`;
}

const notFound = (heading, text) => `<p class="eyebrow">Not found</p><h1>${esc(heading)}</h1><p>${esc(text)}</p><p><a class="button" href="research.html">Browse research</a> <a class="button secondary" href="repositories.html">Browse repositories</a> <a class="button secondary" href="charts.html">Open the Hot 100</a></p>`;

async function init() {
  if (!["research", "repositories"].includes(type) || !id) throw new Error("bad-link");
  const [current, researchItems, repositories, claims] = await Promise.all([fetch(`data/${type}.json`).then(response => response.json()), fetch("data/research.json").then(response => response.json()), fetch("data/repositories.json").then(response => response.json()), fetch("data/claims.json").then(response => response.json())]);
  EvidenceTopics.install(claims);
  const claimsById = Object.fromEntries(claims.map(claim => [claim.id, claim]));
  const item = current.find(candidate => candidate.id === id);
  if (!item) throw new Error("missing-record");
  document.title = `${item.title || item.repository} | StaleToast`;
  document.querySelector("main").innerHTML = type === "research" ? research(item, researchItems, repositories, claimsById) : repository(item, repositories, researchItems, claimsById);
}

init().catch(error => {
  const main = document.querySelector("main");
  if (error && error.message === "bad-link") main.innerHTML = notFound("This link is incomplete.", "A profile link needs a record type and a record ID. Choose a record from one of the catalogs.");
  else if (error && error.message === "missing-record") main.innerHTML = notFound("This profile is missing.", "No record with that ID is in the catalog. The link may be old or mistyped.");
  else main.innerHTML = notFound("The profile could not load.", "The catalog data did not load. Reload the page, or open a catalog and choose the record again.");
});
