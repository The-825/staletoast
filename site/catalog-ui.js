"use strict";
// Pure display helpers for the research and repository catalogs.
// Nothing here reads or writes catalog data: filtering returns a subset in the
// input order, sorting works on a copy, and labels never change a grade.
const CatalogUI = (() => {
  const UNAPPRAISED = "unappraised";
  const PAGE_SIZES = [12, 24, 48];
  const DEFAULT_PAGE_SIZE = 12;
  const titleCase = value => String(value ?? "").replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());

  const DIRECTNESS = {
    D3: {name: "Target-like", note: "Studied work close to the setting this guide cares about."},
    D2: {name: "Adjacent", note: "Studied a nearby setting, so findings may carry over in part."},
    D1: {name: "Analogy", note: "Studied a comparable but different setting. Use it as an analogy."},
    D0: {name: "Conceptual", note: "A concept or argument, not a study of this kind of work."}
  };
  const HORIZON = {
    "not observed": "No time span observed",
    single: "Observed once",
    technical: "Technical evaluation",
    repeated: "Observed repeatedly",
    longitudinal: "Observed over a long period"
  };
  const MECHANISM_STATE = {V: "Visible", P: "Partial", U: "Unknown", N: "Not observed or out of scope"};

  const isAutomated = item => item.appraisal_state === "automated-screen";
  const directnessKey = item => {
    const match = /^D([0-3])/.exec(item.directness ?? "");
    return match ? `D${match[1]}` : null;
  };
  function directnessText(item) {
    const key = directnessKey(item);
    if (!key) return {short: "Not graded yet", note: "No directness grade has been recorded for this record."};
    return {short: DIRECTNESS[key].name, note: DIRECTNESS[key].note};
  }
  const horizonText = item => item.horizon === null || item.horizon === undefined ? "Not graded yet" : (HORIZON[item.horizon] || titleCase(item.horizon));

  // Plain-English evidence depth. Automated checks are never described as appraisals.
  function researchDepth(item) {
    if (isAutomated(item)) return {label: "Abstract relevance check, awaiting appraisal", note: "Matched on the abstract only. Findings are not appraised, and the record has no directness or horizon grade."};
    if (item.review_depth === "screened-structural") return {label: "Structural source screen", note: "The source was screened for structure and graded. This is not a claim that it was fully appraised or independently replicated."};
    if (item.review_depth === "selected-full-text") return {label: "Selected full-text review", note: "Selected parts of the full text were reviewed. This is not independent replication or proof of adoption."};
    if (item.review_depth === "prior-screened-candidate") return {label: "Earlier screened candidate", note: "Retains an earlier source screen. Check the profile for its promotion status and limits."};
    if (item.review_depth === "abstract-only") return {label: "Abstract-level screen", note: "Read at abstract level only. Full text was not reviewed."};
    return {label: titleCase(item.review_depth || "Review depth not recorded"), note: "Review depth as recorded in the catalog."};
  }
  function repositoryDepth(item) {
    if (isAutomated(item) || item.evidence_depth === "readme-relevance-screened") return {label: "README relevance check, awaiting appraisal", note: "An automated check of the README. No mechanism, code, security or reuse-rights appraisal was done, so every mechanism stays unknown."};
    if (item.evidence_depth === "source-assessment") return {label: "Portable record: identity and provenance only", note: "Records who and where the repository is. It is not a mechanism review."};
    if (item.evidence_depth === "readme-screened") return {label: "README screened against a pinned revision", note: "Mechanisms were recorded from the README at a pinned revision. This is not a code review."};
    return {label: titleCase(item.evidence_depth || "Evidence depth not recorded"), note: "Evidence depth as recorded in the catalog."};
  }
  const depthInfo = (type, item) => type === "research" ? researchDepth(item) : repositoryDepth(item);
  const depthValue = (type, item) => type === "research" ? item.review_depth : item.evidence_depth;
  const dateOrNotRecorded = value => value ? String(value) : "not recorded";
  const mechanismState = code => MECHANISM_STATE[code] || "Unknown";
  const mechanismName = key => titleCase(key);

  function searchText(type, item, topicLabel) {
    const topics = (item.claims || []).map(id => topicLabel(id));
    const fields = type === "research"
      ? [item.id, item.title, item.finding, item.impact, item.boundary, item.design, item.familyLabel, item.flags, item.levelEvidence]
      : [item.id, item.repository, item.evidence_note, item.category, item.selection_aspect, item.lifecycle];
    return JSON.stringify([fields, topics]).toLowerCase();
  }
  // Read-only: returns matching items in their input order.
  function filterItems(type, items, state, topicLabel = id => id) {
    const needle = String(state.query || "").trim().toLowerCase();
    return items.filter(item => {
      if (needle && !searchText(type, item, topicLabel).includes(needle)) return false;
      if (state.filter === UNAPPRAISED) { if (!isAutomated(item)) return false; }
      else if (state.filter) {
        if (type === "research" ? directnessKey(item) !== state.filter : item.category !== state.filter) return false;
      }
      if (state.theme && (type === "research" ? item.family : item.lifecycle) !== state.theme) return false;
      if (state.claim && !(item.claims || []).includes(state.claim)) return false;
      if (state.depth && depthValue(type, item) !== state.depth) return false;
      return true;
    });
  }
  // Works on a copy. "rank" keeps the recorded order; "alpha" sorts by name.
  function sortItems(items, sort) {
    const copy = items.slice();
    if (sort === "alpha") return copy.sort((a, b) => (a.title || a.repository).localeCompare(b.title || b.repository));
    const order = item => item.evidenceOrder ?? item.catalogOrder ?? Number.MAX_SAFE_INTEGER;
    return copy.sort((a, b) => order(a) - order(b) || a.id.localeCompare(b.id));
  }
  function paginate(total, page, size = DEFAULT_PAGE_SIZE) {
    const pageSize = PAGE_SIZES.includes(Number(size)) ? Number(size) : DEFAULT_PAGE_SIZE;
    const pages = Math.max(1, Math.ceil(total / pageSize));
    const requested = Number.parseInt(page, 10);
    const current = Math.min(Math.max(Number.isFinite(requested) ? requested : 1, 1), pages);
    return {
      page: current, pages, size: pageSize,
      start: total === 0 ? 0 : (current - 1) * pageSize + 1,
      end: Math.min(total, current * pageSize),
      hasPrev: current > 1, hasNext: current < pages
    };
  }
  const countText = (total, matching, range, noun = "records") =>
    `${matching} of ${total} ${noun} match. ${matching ? `Showing ${range.start} to ${range.end}.` : "Showing none."}`;
  function activeFilters(entries) {
    return entries.filter(entry => String(entry.value || "").trim()).map(entry => `${entry.name}: ${entry.text ?? entry.value}`);
  }
  const filterSummaryText = parts => parts.length ? `Active filters. ${parts.join(". ")}.` : "No filters are active.";

  return {
    UNAPPRAISED, PAGE_SIZES, DEFAULT_PAGE_SIZE, DIRECTNESS, titleCase, isAutomated, directnessKey, directnessText, horizonText,
    researchDepth, repositoryDepth, depthInfo, depthValue, dateOrNotRecorded, mechanismState, mechanismName,
    filterItems, sortItems, paginate, countText, activeFilters, filterSummaryText
  };
})();
