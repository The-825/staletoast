"use strict";
function latestEditionText(chartData) {
  const date = chartData && chartData.latest && chartData.latest.edition_date;
  return /^\d{4}-\d{2}-\d{2}$/.test(String(date))
    ? `Latest edition: ${date}. The date marks an editorial reevaluation, not the freshness of each source.`
    : "";
}
async function showEdition() {
  const target = document.querySelector("#edition-date");
  const response = await fetch("data/charts.json", {cache: "no-cache"});
  if (!response.ok) throw new Error("Chart data unavailable");
  const text = latestEditionText(await response.json());
  if (text) target.textContent = text;
}
if (typeof document !== "undefined" && document.querySelector("#edition-date")) showEdition().catch(() => {});

function escapeHomeHtml(value) {
  return String(value === null || value === undefined ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function readingPathType(kind) {
  return kind === "research" ? "research" : kind === "repository" ? "repositories" : "";
}
const READING_PATH_DEPTH_LABELS = {
  "screened-structural": {research: "Structure screened", repository: "Repository structure screened, not run"},
  "selected-full-text": {research: "Full text read", repository: "Full text read"},
  "abstract-only": {research: "Abstract read only", repository: "Summary read only"},
  "readme-screened": {research: "Summary screened", repository: "README screened"}
};
function readingPathDepthLabel(kind, depth) {
  const labels = READING_PATH_DEPTH_LABELS[String(depth)];
  if (!labels) return "Depth stated in reference details";
  return kind === "repository" ? labels.repository : labels.research;
}
function readingPathPlainText(value) {
  return String(value === null || value === undefined ? "" : value)
    .replace(/\(\s*(?:CI|R)-\d+\s*\)/g, "")
    .replace(/\b(?:CI|R)-\d+\b/g, "")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:])/g, "$1")
    .trim();
}
function readingPathCounterevidenceText(counterevidence) {
  if (!counterevidence) return "";
  if (typeof counterevidence === "string") return readingPathPlainText(counterevidence);
  if (!Array.isArray(counterevidence) || !counterevidence.length) return "";
  return counterevidence
    .map((entry) => {
      if (typeof entry === "string") return readingPathPlainText(entry);
      if (!entry || typeof entry !== "object") return "";
      const parts = [];
      if (typeof entry.observed_date === "string" && entry.observed_date.trim()) parts.push(`Observed ${entry.observed_date.trim()}`);
      if (typeof entry.state === "string" && entry.state.trim()) parts.push(`state: ${entry.state.trim()}`);
      if (typeof entry.boundary === "string" && entry.boundary.trim()) parts.push(entry.boundary.trim());
      const sentenceText = readingPathPlainText(parts.join(". "));
      if (!sentenceText) return "";
      return /[.!?]$/.test(sentenceText) ? sentenceText : `${sentenceText}.`;
    })
    .filter(Boolean)
    .join(" ");
}
function readingPathSelectionHtml(selection) {
  const type = readingPathType(selection.kind);
  const kindLabel = selection.kind === "repository" ? "Repository" : selection.kind === "research" ? "Research" : "Record";
  const facts = [
    ["Why it is here", selection.why_selected],
    ["Takeaway", selection.takeaway],
    ["Limits", selection.limits],
    ["Counterevidence", readingPathCounterevidenceText(selection.counterevidence)]
  ].filter(([, text]) => readingPathPlainText(text))
    .map(([label, text]) => `<dt>${escapeHomeHtml(label)}</dt><dd>${escapeHomeHtml(readingPathPlainText(text))}</dd>`)
    .join("");
  const actions = [];
  if (type && selection.id !== undefined && selection.id !== null && String(selection.id)) {
    actions.push(`<a class="button" href="detail.html?type=${type}&amp;id=${encodeURIComponent(String(selection.id))}">Read the record</a>`);
  }
  const sourceUrl = String(selection.source_url || "");
  if (/^https:\/\/[^\s"'<>]+$/.test(sourceUrl)) {
    actions.push(`<a class="button secondary" href="${escapeHomeHtml(sourceUrl)}" rel="noopener">Original source</a>`);
  }
  return `<article class="card record-card">`
    + `<p class="badges"><span class="pill">${escapeHomeHtml(kindLabel)}</span><span class="pill">${escapeHomeHtml(readingPathDepthLabel(selection.kind, selection.evidence_depth))}</span></p>`
    + `<h4>${escapeHomeHtml(readingPathPlainText(selection.title) || "Untitled record")}</h4>`
    + (facts ? `<dl class="facts">${facts}</dl>` : "")
    + (actions.length ? `<div class="card-actions">${actions.join("")}</div>` : "")
    + `<details class="reference"><summary>Reference details</summary>`
    + `<p>Record ID: <code>${escapeHomeHtml(selection.id)}</code></p>`
    + `<p>Evidence depth code: <code>${escapeHomeHtml(selection.evidence_depth)}</code></p>`
    + `</details></article>`;
}
function renderReadingPaths(guide) {
  const empty = {metaText: "", html: ""};
  if (!(guide && guide.schema_version === 1 && Array.isArray(guide.collections) && guide.collections.length > 0)) return empty;
  const blocks = guide.collections
    .filter((collection) => collection && Array.isArray(collection.selections))
    .map((collection) => {
      const cards = collection.selections
        .filter((selection) => selection && typeof selection === "object")
        .map(readingPathSelectionHtml);
      if (!cards.length) return "";
      return `<div class="section">`
        + `<h3>${escapeHomeHtml(readingPathPlainText(collection.title) || "Reading path")}</h3>`
        + (readingPathPlainText(collection.description) ? `<p>${escapeHomeHtml(readingPathPlainText(collection.description))}</p>` : "")
        + `<div class="grid record-cards">${cards.join("")}</div></div>`;
    })
    .filter(Boolean);
  if (!blocks.length) return empty;
  const date = /^\d{4}-\d{2}-\d{2}$/.test(String(guide.date)) ? ` dated ${guide.date}` : "";
  const metaText = `Editorial reading paths${date}. Selected from existing appraisals. Not a quality score, a ranking or an adoption recommendation.`;
  return {metaText, html: blocks.join("")};
}
async function showReadingPaths() {
  const target = document.querySelector("#reading-paths");
  const meta = document.querySelector("#reading-paths-meta");
  const response = await fetch("data/reader-guide.json", {cache: "no-cache"});
  if (!response.ok) throw new Error("Reading paths unavailable");
  const result = renderReadingPaths(await response.json());
  if (!result.html) return;
  target.innerHTML = result.html;
  if (meta && result.metaText) meta.textContent = result.metaText;
}
if (typeof document !== "undefined" && document.querySelector("#reading-paths")) showReadingPaths().catch(() => {});
