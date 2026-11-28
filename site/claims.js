"use strict";
const escClaim = (value = "") => String(value ?? "").replace(/[&<>'"]/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[character]));

function countRecordsByClaim(records) {
  const counts = {};
  if (!Array.isArray(records)) return counts;
  for (const record of records) {
    if (!Array.isArray(record.claims)) continue;
    for (const cid of record.claims) {
      counts[cid] = (counts[cid] || 0) + 1;
    }
  }
  return counts;
}

function componentsForClaim(scopeMap, claimId) {
  if (!scopeMap || !Array.isArray(scopeMap.components)) return [];
  return scopeMap.components.filter(component => Array.isArray(component.related_claims) && component.related_claims.includes(claimId));
}

function renderClaimActions(claimId, counts) {
  const encoded = encodeURIComponent(claimId);
  const resCount = counts && counts.research ? counts.research[claimId] || 0 : null;
  const repoCount = counts && counts.repositories ? counts.repositories[claimId] || 0 : null;
  const resAction = resCount === 0
    ? `<span class="pill">0 matching research records</span>`
    : `<a class="button" href="research.html?claim=${encoded}">${escClaim(resCount === null ? "Browse matching research" : `Browse research (${resCount})`)}</a>`;
  const repoAction = repoCount === 0
    ? `<span class="pill">0 matching repositories</span>`
    : `<a class="button secondary" href="repositories.html?claim=${encoded}">${escClaim(repoCount === null ? "Browse matching repositories" : `Browse repositories (${repoCount})`)}</a>`;
  return `<div class="actions claim-actions">${resAction}${repoAction}</div>`;
}

function renderClaimComponents(scopeMap, claimId) {
  const matches = componentsForClaim(scopeMap, claimId);
  if (!scopeMap) return "";
  if (!matches.length) {
    return `<dt>Scope components</dt><dd>No search component currently lists this topic as a pointer.</dd>`;
  }
  const items = matches.map(component => {
    const statusTone = component.status === "established" ? "pill" : "pill unscreened-pill";
    return `<li><strong>${escClaim(component.label)}</strong> <span class="${statusTone}">${escClaim(component.status_label)}</span><br><small>${escClaim(component.comparison_question)}</small></li>`;
  }).join("");
  const meaning = scopeMap.related_claims_meaning || "A pointer to topics a component is likely to inform, not an evidence link.";
  return `<dt>Scope components</dt><dd><ul class="plain-list scope-component-list">${items}</ul><small class="scope-note">${escClaim(meaning)}</small></dd>`;
}

function inspector(item, context = {}) {
  return `<p class="eyebrow">${escClaim(item.theme)}</p><h2>${escClaim(item.readerLabel)}</h2><p>${escClaim(item.title)}</p><p class="lede">${escClaim(EvidenceTopics.text(item.claim))}</p>${renderClaimActions(item.id, context.counts)}<dl><dt>Evidence profile</dt><dd>${escClaim(EvidenceTopics.text(item.profile))}</dd><dt>Disposition</dt><dd>${escClaim(EvidenceTopics.text(item.disposition))}</dd><dt>Support</dt><dd>${escClaim(EvidenceTopics.text(item.supports))}</dd><dt>What would disprove it</dt><dd>${escClaim(EvidenceTopics.text(item.nullCase))}</dd><dt>Next test</dt><dd>${escClaim(EvidenceTopics.text(item.nextTest))}</dd>${renderClaimComponents(context.scopeMap, item.id)}</dl><details class="reference"><summary>Evidence reference</summary><p>Topic ID: <code>${escClaim(item.id)}</code></p></details>`;
}

function renderScopeMapSection(scopeMap) {
  if (!scopeMap || !Array.isArray(scopeMap.components) || !scopeMap.components.length) return "";
  const establishedCount = scopeMap.components.filter(c => c.status === "established").length;
  const addedCount = scopeMap.components.filter(c => c.status === "added-unscreened").length;
  const cards = scopeMap.components.map(component => {
    const unscreened = component.status !== "established";
    const badgeClass = unscreened ? "pill unscreened-pill" : "pill depth";
    const claimButtons = (component.related_claims || []).map(cid =>
      `<a class="pill" data-select-claim="${escClaim(cid)}" href="#${escClaim(cid.toLowerCase())}">${escClaim(EvidenceTopics.label(cid))}</a>`
    ).join("");
    const boundary = component.boundary ? `<p class="note">${escClaim(component.boundary)}</p>` : "";
    return `<article class="record-card scope-card"><p class="badges"><span class="${badgeClass}">${escClaim(component.status_label)}</span></p><h3>${escClaim(component.label)}</h3><p>${escClaim(component.definition)}</p><dl class="facts"><div><dt>Comparison question</dt><dd>${escClaim(component.comparison_question)}</dd></div></dl>${boundary}${claimButtons ? `<p class="topics"><span class="topics-label">Related topics</span> ${claimButtons}</p>` : ""}<details class="reference"><summary>Reference details</summary><p>Component ID: <code>${escClaim(component.id)}</code></p><p>Effective since: <code>${escClaim(component.since)}</code></p></details></article>`;
  }).join("");
  return `<section class="section" aria-labelledby="scope-map-title"><p class="eyebrow">Search scope · Effective ${escClaim(scopeMap.effective_date)}</p><h2 id="scope-map-title">Components of collaborative intelligence.</h2><p class="lede">${escClaim(scopeMap.purpose)}</p><p class="note">${establishedCount} components are established in the baseline routing record. ${addedCount} components were added to scope and are not yet screened: they hold no screened source count, grade or finding. ${escClaim(scopeMap.authority)}</p><div class="record-cards">${cards}</div></section>`;
}

async function fetchOptionalJson(url) {
  try {
    const response = await fetch(url);
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

async function loadClaimsPage() {
  const target = document.querySelector("#claims");
  try {
    const response = await fetch("data/claims.json");
    if (!response.ok) throw new Error("Claims unavailable");
    const [claims, research, repositories, scopeMap] = await Promise.all([
      response.json(),
      fetchOptionalJson("data/research.json"),
      fetchOptionalJson("data/repositories.json"),
      fetchOptionalJson("data/scope-map.json")
    ]);
    EvidenceTopics.install(claims);
    const context = {
      counts: research && repositories ? {
        research: countRecordsByClaim(research),
        repositories: countRecordsByClaim(repositories)
      } : null,
      scopeMap
    };
    const themes = [...new Set(claims.map(item => item.theme))];
    const nodes = themes.map(theme => `<section class="claim-cluster"><h2>${escClaim(theme)}</h2><div>${claims.filter(item => item.theme === theme).map(item => `<button class="claim-node" type="button" data-claim="${escClaim(item.id)}"><strong>${escClaim(item.readerLabel)}</strong></button>`).join("")}</div></section>`).join("");
    target.innerHTML = `<div class="claim-graph" aria-label="Interactive landscape of seventeen collaborative-intelligence claims">${nodes}<div class="claim-core" aria-hidden="true">StaleToast<br><span>17 bounded claims</span></div></div><aside id="claim-inspector" class="detail claim-inspector">${inspector(claims[0], context)}</aside>${renderScopeMapSection(scopeMap)}`;
    const byId = Object.fromEntries(claims.map(item => [item.id, item]));
    const select = id => {
      if (!byId[id]) return;
      document.querySelectorAll(".claim-node").forEach(node => node.classList.toggle("selected", node.dataset.claim === id));
      document.querySelector("#claim-inspector").innerHTML = inspector(byId[id], context);
      if (typeof history !== "undefined" && typeof history.replaceState === "function") {
        history.replaceState(null, "", `#${id.toLowerCase()}`);
      }
    };
    document.querySelectorAll(".claim-node").forEach(node => node.addEventListener("click", () => select(node.dataset.claim)));
    document.querySelectorAll("[data-select-claim]").forEach(link => link.addEventListener("click", event => {
      const cid = link.getAttribute("data-select-claim");
      if (byId[cid]) {
        event.preventDefault();
        select(cid);
        const panel = document.querySelector("#claim-inspector");
        if (panel && panel.scrollIntoView) panel.scrollIntoView({block: "nearest"});
      }
    }));
    const initial = ((typeof location !== "undefined" && location.hash) || "").slice(1).toUpperCase();
    select(byId[initial] ? initial : claims[0].id);
  } catch {
    target.textContent = "The claim landscape could not load. Use the public repository record instead.";
  }
}

if (typeof document !== "undefined" && document.querySelector("#claims")) {
  loadClaimsPage();
}
