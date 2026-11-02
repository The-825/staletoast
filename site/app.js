const type = document.body.dataset.catalog;
const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
}[char]));
const UNAPPRAISED = "unappraised";
const APPRAISAL_STATES = ["automated-screen", "source-screened"];
let items = [];
let claimsById = {};

const detailLink = (kind, id, label) =>
  `<a href="detail.html?type=${kind}&id=${encodeURIComponent(id)}">${escapeHtml(label)}</a>`;
const claimLinks = claims => claims.map(claim => `<a class="pill" href="claims.html#${claim.toLowerCase()}">${escapeHtml(EvidenceTopics.label(claim))}</a>`).join("");
const label = value => value.replaceAll("-", " ").replace(/\b\w/g, letter => letter.toUpperCase());

const isAutomated = item => item.appraisal_state === "automated-screen";

function researchRow(item) {
  const automated = isAutomated(item);
  return `<tr>
    <td class="rank">${escapeHtml(item.id)}</td>
    <td class="rank">${automated ? "Unranked<br><small>(automated screen)</small>" : `${item.evidenceOrder}<small> / ${item.evidenceOrderCount}</small>`}</td>
    <td><strong>${detailLink("research", item.id, item.title)}</strong>${item.record_state === "candidate-not-promoted" ? '<br><span class="pill">Candidate, not promoted</span>' : ""}${automated ? '<br><span class="pill">Screened (automated), awaiting appraisal</span>' : ""}<br><a href="${escapeHtml(item.url)}">Original source</a></td>
    <td><strong>${automated ? "Not appraised" : `${item.directnessValue} / 3`}</strong>${automated ? "" : `<br><span class="pill">${escapeHtml(item.directness)}</span>`}</td>
    <td><strong>${automated ? "Not appraised" : `${item.horizonValue} / 3`}</strong>${automated ? "" : `<br><span class="pill">${escapeHtml(item.horizon)}</span>`}</td>
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
    <td><strong>${automated ? "Screened (automated)" : "Reviewed"} ${escapeHtml(item.lastReviewed)}</strong><br><span class="pill">${escapeHtml(label(item.evidence_depth))}</span></td>
    <td>${escapeHtml(EvidenceTopics.text(item.evidence_note))}</td>
  </tr>`;
}

function render() {
  const query = document.querySelector("#search").value.trim().toLowerCase();
  const filter = document.querySelector("#filter").value;
  const theme = document.querySelector("#theme").value;
  const claim = document.querySelector("#claim").value;
  const sort = document.querySelector("#sort").value;
  let output = items.filter(item => JSON.stringify([item, item.claims.map(id => EvidenceTopics.label(id))]).toLowerCase().includes(query));
  if (filter === UNAPPRAISED) output = output.filter(isAutomated);
  else if (filter) output = output.filter(item => type === "research" ? typeof item.directness === "string" && item.directness.startsWith(filter) : item.category === filter);
  if (theme) output = output.filter(item => type === "research" ? item.family === theme : item.lifecycle === theme);
  if (claim) output = output.filter(item => item.claims.includes(claim));
  if (sort === "alpha") output.sort((a, b) => (a.title || a.repository).localeCompare(b.title || b.repository));
  else {
    // Unranked automated screens (evidenceOrder null) follow every ranked record.
    const order = item => item.evidenceOrder ?? item.catalogOrder ?? Number.MAX_SAFE_INTEGER;
    output.sort((a, b) => order(a) - order(b) || a.id.localeCompare(b.id));
  }
  document.querySelector("tbody").innerHTML = output.map(type === "research" ? researchRow : repositoryRow).join("");
  document.querySelector("#count").textContent = `${output.length} of ${items.length}`;
  document.querySelector(".empty").style.display = output.length ? "none" : "block";
}

function addOptions(control, values) {
  control.innerHTML += values.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(label(value))}</option>`).join("");
}

async function catalog() {
  if (!type) return;
  const response = await fetch(`data/${type}.json`);
  if (!response.ok) throw new Error("Catalog data unavailable");
  items = await response.json();
  if (items.some(item => !APPRAISAL_STATES.includes(item.appraisal_state))) throw new Error("Unknown appraisal state");
  if (type === "research") {
    document.querySelector(".catalog-head .eyebrow").textContent =
      `Research Trail · ${items.length} source records`;
    const automated = items.filter(isAutomated).length;
    document.querySelector(".catalog-head .lede").textContent =
      `${items.length - automated} records retain their existing review depth and evidence order. ${automated} are Unranked (automated screen): abstract relevance screens, intake awaiting appraisal, with no directness or horizon grade, listed after the ranked records. Screening finds material to inspect; it does not validate findings or select the Hot 100.`;
  } else {
    const detailed = items.filter(item => item.evidence_depth === "readme-screened").length;
    const portable = items.filter(item => item.evidence_depth === "source-assessment").length;
    const relevance = items.filter(item => item.evidence_depth === "readme-relevance-screened").length;
    if (detailed + portable + relevance !== items.length) throw new Error("Unknown repository evidence depth");
    document.querySelector(".catalog-head .eyebrow").textContent =
      `Repository Trail · ${items.length} repository records`;
    document.querySelector(".catalog-head .lede").textContent =
      `${detailed} repositories have pinned mechanism reviews, ${portable} retain portable assessment evidence, and ${relevance} are Screened (automated) by README relevance only, not reviewed, and are unvetted third-party repositories awaiting appraisal. Mechanisms remain unknown for relevance screens. Stars are popularity only and do not establish quality; popularity positions are relative to the current collection and can change as it grows.`;
  }
  const claims = await fetch("data/claims.json").then(result => result.json());
  EvidenceTopics.install(claims);
  claimsById = Object.fromEntries(claims.map(item => [item.id, item]));
  addOptions(document.querySelector("#filter"), type === "research"
    ? ["D3", "D2", "D1", "D0"]
    : [...new Set(items.map(item => item.category))].sort());
  if (items.some(isAutomated)) document.querySelector("#filter").innerHTML += `<option value="${UNAPPRAISED}">Unappraised (automated screen)</option>`;
  addOptions(document.querySelector("#theme"), type === "research"
    ? [...new Set(items.map(item => item.family))].sort()
    : [...new Set(items.map(item => item.lifecycle))].sort());
  const claimControl = document.querySelector("#claim");
  claimControl.innerHTML += [...new Set(items.flatMap(item => item.claims))].sort().map(value => `<option value="${escapeHtml(value)}">${escapeHtml(EvidenceTopics.label(value))}</option>`).join("");
  document.querySelectorAll("input, select").forEach(control => control.addEventListener("input", render));
  render();
}

catalog().catch(() => {
  const count = document.querySelector("#count");
  if (count) count.textContent = "Unavailable";
  const empty = document.querySelector(".empty");
  if (empty) {
    empty.textContent = "The catalog could not load. Use the repository source files instead.";
    empty.style.display = "block";
  }
});
