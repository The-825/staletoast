"""Visitor UX checks for the StaleToast site: navigation, routes, and catalog behavior.

Behavior tests run the real browser scripts in a Node VM against a small fake DOM
and the real data files. They need `node` and are skipped without it. No test here
runs a browser; keyboard, layout and touch checks stay with the browser pass.
"""
import html as htmllib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

SITE = Path(__file__).resolve().parent
NAV = ["Home", "Research", "Repositories", "Hot 100", "How to read", "Breadcrumbs", "The 825"]
CURRENT = {"index.html": "Home", "research.html": "Research", "repositories.html": "Repositories",
           "charts.html": "Hot 100", "methodology.html": "How to read"}
HARNESS = r'''
const fs = require("fs"), vm = require("vm"), path = require("path");
const site = process.argv[1];
const read = f => fs.readFileSync(path.join(site, f), "utf8");
const data = n => JSON.parse(read("data/" + n + ".json"));

function makeDom(pageFile, catalog) {
  const html = read(pageFile);
  const els = {};
  const state = {focus: null};
  function make(sel) {
    const id = sel.startsWith("#") ? sel.slice(1) : null;
    if (id && !html.includes('id="' + id + '"')) throw new Error("missing element " + sel);
    const tag = id ? new RegExp('<[^>]*id="' + id + '"[^>]*>').exec(html)[0] : "";
    const el = {
      sel, value: "", hidden: /\shidden[\s>]/.test(tag), disabled: /\sdisabled[\s>]/.test(tag), textContent: "", _html: "", attrs: {}, listeners: {},
      addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); },
      setAttribute(k, v) { this.attrs[k] = v; }, focus() { state.focus = sel; }, scrollIntoView() {},
      get innerHTML() { return this._html; }, set innerHTML(v) { this._html = String(v); },
      get options() { return [...this._html.matchAll(/<option value="([^"]*)"[^>]*>([^<]*)<\/option>/g)].map(m => ({value: m[1], text: m[2]})); },
      get selectedIndex() { const i = this.options.findIndex(o => o.value === this.value); return i < 0 ? 0 : i; }
    };
    if (id) {
      const inner = new RegExp('<select id="' + id + '">([\\s\\S]*?)</select>').exec(html);
      if (inner) {
        el._html = inner[1];
        const chosen = /<option value="([^"]*)" selected/.exec(inner[1]);
        el.value = chosen ? chosen[1] : (el.options[0] ? el.options[0].value : "");
      }
    }
    return el;
  }
  const get = sel => els[sel] || (els[sel] = make(sel));
  const document = {body: {dataset: {catalog}}, title: "", querySelector: get, querySelectorAll: () => []};
  const fire = (sel, type) => { for (const f of (get(sel).listeners[type] || [])) f({}); };
  return {document, get, fire, state};
}
function context(document, extra) {
  const sandbox = Object.assign({
    URLSearchParams, setTimeout, console, location: {search: "", hash: ""},
    fetch: async url => {
      const file = path.join(site, url);
      if (!fs.existsSync(file)) return {ok: false, json: async () => ({})};
      return {ok: true, json: async () => JSON.parse(fs.readFileSync(file, "utf8"))};
    }
  }, document ? {document} : {}, extra || {});
  return vm.createContext(sandbox);
}
const run = (ctx, file) => vm.runInContext(read(file), ctx, {filename: file});
async function until(fn) { for (let i = 0; i < 300; i++) { if (fn()) return true; await new Promise(r => setTimeout(r, 10)); } return false; }

async function runCatalog(catalog, fail) {
  const dom = makeDom(catalog + ".html", catalog);
  const ctx = context(dom.document, fail ? {fetch: async () => { throw new Error("offline"); }} : {});
  for (const f of ["topics.js", "catalog-ui.js", "app.js"]) run(ctx, f);
  const get = dom.get;
  await until(() => get("#cards").innerHTML.length > 0 || get("#load-error").hidden === false);
  const snap = () => ({
    cards: (get("#cards").innerHTML.match(/class="record-card"/g) || []).length,
    count: get("#count").textContent, filters: get("#filter-summary").textContent,
    emptyHidden: get("#empty").hidden, pagerHidden: get("#pager").hidden,
    prevDisabled: get("#prev").disabled, nextDisabled: get("#next").disabled, pageStatus: get("#page-status").textContent,
    resetDisabled: get("#reset").disabled, cardsHidden: get("#cards").hidden, tableHidden: get("#table-view").hidden,
    loadErrorHidden: get("#load-error").hidden, focus: dom.state.focus
  });
  const out = {initial: snap(), cardsHtml: get("#cards").innerHTML};
  if (fail) return out;
  out.options = {filter: get("#filter").options, theme: get("#theme").options, depth: get("#depth").options};
  out.ledeText = dom.document.querySelector(".catalog-head .lede").textContent;
  dom.fire("#next", "click"); out.page2 = snap();
  dom.fire("#prev", "click"); out.backToPage1 = snap();
  get("#search").value = "zzzzqqqq"; dom.fire("#search", "input"); out.noMatch = snap();
  dom.fire("#empty-reset", "click"); out.afterReset = snap(); out.searchAfterReset = get("#search").value;
  get("#page-size").value = "24"; dom.fire("#page-size", "change"); out.size24 = snap();
  get("#page-size").value = "12"; dom.fire("#page-size", "change");
  get("#filter").value = catalog === "research" ? "D3" : get("#filter").options[1].value; dom.fire("#filter", "change"); out.filtered = snap();
  dom.fire("#reset", "click"); out.afterResetButton = snap(); out.filterAfterReset = get("#filter").value;
  if (catalog === "research") get("#filter").value = "unappraised"; else get("#depth").value = "readme-relevance-screened";
  dom.fire(catalog === "research" ? "#filter" : "#depth", "change"); out.automated = snap(); out.automatedHtml = get("#cards").innerHTML;
  dom.fire("#reset", "click");
  dom.fire("#view-toggle", "click"); out.table = snap(); out.togglePressed = get("#view-toggle").attrs["aria-pressed"];
  return out;
}

function pure() {
  const ctx = context(null);
  run(ctx, "topics.js"); run(ctx, "catalog-ui.js");
  const UI = vm.runInContext("CatalogUI", ctx);
  const research = data("research");
  const before = JSON.stringify(research);
  const everything = UI.sortItems(UI.filterItems("research", research, {}), "rank");
  const matched = UI.sortItems(UI.filterItems("research", research, {query: "agent"}), "rank");
  const order = new Map(everything.map((item, index) => [item.id, index]));
  const positions = matched.map(item => order.get(item.id));
  const automated = research.filter(UI.isAutomated);
  return {
    untouched: JSON.stringify(research) === before,
    total: research.length, everythingLength: everything.length,
    recordedOrderIds: everything.slice(0, 5).map(i => i.id),
    expectedFirstIds: research.filter(i => i.evidenceOrder !== null).sort((a, b) => a.evidenceOrder - b.evidenceOrder).slice(0, 5).map(i => i.id),
    matchedLength: matched.length, subsequence: positions.every((p, i) => i === 0 || positions[i - 1] < p),
    automatedCount: automated.length,
    nullGradesStayNull: automated.every(i => i.directnessValue === null && UI.directnessKey(i) === null && UI.directnessText(i).short === "Not graded yet"),
    automatedDepth: UI.researchDepth(automated[0]).label,
    repoLabels: ["readme-relevance-screened", "source-assessment", "readme-screened"].map(v => UI.repositoryDepth({evidence_depth: v}).label),
    d3count: UI.filterItems("research", research, {filter: "D3"}).length,
    d3expected: research.filter(i => /^D3/.test(i.directness || "")).length,
    p1: UI.paginate(500, 1, 12), p0: UI.paginate(0, 5, 12), pClamp: UI.paginate(25, 9, 12), pBadSize: UI.paginate(40, 1, 999),
    pLast: UI.paginate(25, 3, 12), count: UI.countText(500, 37, UI.paginate(37, 2, 12), "research records"),
    zeroCount: UI.countText(500, 0, UI.paginate(0, 1, 12), "research records")
  };
}

function charts() {
  const ctx = context(null);
  for (const f of ["topics.js", "catalog-ui.js", "charts.js"]) run(ctx, f);
  vm.runInContext("EvidenceTopics.install(" + JSON.stringify(data("claims")) + ")", ctx);
  const all = data("charts");
  const entries = all.latest.charts.research.entries;
  const repoEntry = all.latest.charts.repositories.entries.find(e => e.snapshot_commit) || all.latest.charts.repositories.entries[0];
  const pieces = html => { const cut = html.indexOf('<details class="reference">'); return [html.slice(0, cut), html.slice(cut)]; };
  const research = ctx.chartItem("research", entries[0]);
  const repo = ctx.chartItem("repositories", repoEntry);
  const none = ctx.filterChartEntries(entries, "zzzzqqqq", id => id);
  const some = ctx.filterChartEntries(entries, "", id => id);
  return {
    researchPrimary: pieces(research)[0], researchReference: pieces(research)[1], researchId: entries[0].id,
    repoPrimary: pieces(repo)[0], repoReference: pieces(repo)[1], repoId: repoEntry.id, repoCommit: repoEntry.snapshot_commit || null,
    noneLength: none.length, allLength: some.length, entriesLength: entries.length,
    positionsKept: some.map(e => e.position).join() === entries.map(e => e.position).join(),
    movement: [ctx.chartMovement({entry_state: "new"}), ctx.chartMovement({entry_state: "continuing", movement: 2}), ctx.chartMovement({entry_state: "continuing", movement: -3}), ctx.chartMovement({entry_state: "continuing", movement: 0})]
  };
}

async function detail(search) {
  const mainEl = {innerHTML: ""};
  const document = {title: "", querySelector: () => mainEl};
  const ctx = context(document, {location: {search}});
  for (const f of ["topics.js", "catalog-ui.js", "detail.js"]) run(ctx, f);
  await until(() => mainEl.innerHTML !== "");
  return mainEl.innerHTML;
}

(async () => {
  const result = {
    research: await runCatalog("research"), repositories: await runCatalog("repositories"),
    researchFail: await runCatalog("research", true), pure: pure(), charts: charts(),
    detailResearch: await detail("?type=research&id=012"), detailRepo: await detail("?type=repositories&id=R-242"),
    detailAutomated: await detail("?type=research&id=C-026"),
    detailMissing: await detail("?type=research&id=NOPE"), detailBad: await detail("?type=other"),
    homeText: vm.runInContext("latestEditionText({latest: {edition_date: '2026-11-02'}})", (() => { const c = context(null); run(c, "home.js"); return c; })()),
    homeBad: vm.runInContext("latestEditionText({})", (() => { const c = context(null); run(c, "home.js"); return c; })())
  };
  console.log(JSON.stringify(result));
})().catch(error => { console.error(error); process.exit(1); });
'''


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.nav, self.scripts, self._in_nav, self._href, self._text, self.current = [], [], [], False, None, "", []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == "Primary":
            self._in_nav = True
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
            if self._in_nav:
                self._href, self._text = attrs["href"], ""
                if attrs.get("aria-current") == "page":
                    self.current.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])

    def handle_data(self, data):
        if self._href is not None:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.nav.append((self._text.strip(), self._href))
            self._href = None
        if tag == "nav":
            self._in_nav = False


def parse(name):
    refs = Refs()
    refs.feed((SITE / name).read_text(encoding="utf-8"))
    return refs


class StaticTests(unittest.TestCase):
    def test_every_page_has_the_same_short_navigation(self):
        for page in sorted(SITE.glob("*.html")):
            refs = parse(page.name)
            self.assertEqual(NAV, [text for text, _ in refs.nav], page.name)
            self.assertIn(("The 825", "https://the825.co/"), refs.nav, page.name)
            if page.name in CURRENT:
                labels = [text for text, href in refs.nav if href in refs.current]
                self.assertEqual([CURRENT[page.name]], labels, page.name)
            else:
                self.assertEqual([], refs.current, page.name)

    def test_index_is_a_distinct_home_not_a_chart(self):
        index = (SITE / "index.html").read_text(encoding="utf-8")
        refs = parse("index.html")
        for needed in ("research.html", "repositories.html", "charts.html"):
            self.assertIn(needed, refs.links)
        self.assertTrue(any(link.startswith("https://the-825.github.io/breadcrumbs/") for link in refs.links))
        self.assertNotIn("chart-list", index)
        self.assertNotIn("charts.js", index)
        self.assertNotIn("catalog-ui.js", index)
        self.assertIn("quality certification", index)
        self.assertEqual(1, len(refs.scripts))
        self.assertRegex(refs.scripts[0], r"^home\.js\?v=\d{8}-\d+$")

    def test_scripts_share_one_cache_version_and_resolve(self):
        versions = set()
        for page in SITE.glob("*.html"):
            for src in parse(page.name).scripts:
                name, _, query = src.partition("?")
                self.assertTrue((SITE / name).is_file(), (page.name, src))
                if page.name in ("index.html", "research.html", "repositories.html", "charts.html", "detail.html"):
                    versions.add(query)
        for name in ("research.html", "repositories.html", "charts.html", "detail.html"):
            scripts = parse(name).scripts
            self.assertTrue(scripts)
            self.assertTrue(all(re.search(r"\?v=\d{8}-\d+$", src) for src in scripts), name)
        self.assertEqual(1, len(versions), versions)

    def test_catalog_pages_have_the_required_controls(self):
        for name in ("research.html", "repositories.html"):
            page = (SITE / name).read_text(encoding="utf-8")
            for ident in ("search", "filter", "theme", "claim", "depth", "sort", "page-size", "reset", "prev", "next",
                          "empty-reset", "load-error", "view-toggle", "page-status", "filter-summary"):
                self.assertIn(f'id="{ident}"', page, (name, ident))
            self.assertRegex(page, r'id="count"[^>]*role="status"')
            self.assertIn("source-dispositions.json", page)
            self.assertIn("not a quality certification", page)

    def test_pages_do_not_use_em_dashes(self):
        for pattern in ("*.html", "*.js", "*.css"):
            for path in SITE.glob(pattern):
                self.assertNotIn(chr(0x2014), path.read_text(encoding="utf-8"), path.name)

    def test_primary_chart_markup_has_no_commit_prefix_expression(self):
        script = (SITE / "charts.js").read_text(encoding="utf-8")
        self.assertNotIn("slice(0, 8)", script)
        self.assertNotIn("Source ${", script)


@unittest.skipUnless(shutil.which("node"), "node is required for behavior tests")
class BehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completed = subprocess.run(["node", "-e", HARNESS, str(SITE)], capture_output=True, text=True, timeout=120)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)
        cls.result = json.loads(completed.stdout.strip().splitlines()[-1])
        cls.research = json.loads((SITE / "data/research.json").read_text(encoding="utf-8"))
        cls.repositories = json.loads((SITE / "data/repositories.json").read_text(encoding="utf-8"))

    def test_default_view_is_twelve_cards_with_separate_counts(self):
        for kind, rows in (("research", self.research), ("repositories", self.repositories)):
            initial = self.result[kind]["initial"]
            self.assertEqual(min(12, len(rows)), initial["cards"])
            self.assertIn(f"{len(rows)} of {len(rows)}", initial["count"])
            self.assertIn("Showing 1 to 12.", initial["count"])
            self.assertTrue(initial["prevDisabled"])
            self.assertFalse(initial["nextDisabled"])
            self.assertEqual("No filters are active.", initial["filters"])
            self.assertTrue(initial["resetDisabled"])
            self.assertTrue(initial["tableHidden"])

    def test_next_and_previous_move_the_visible_range(self):
        for kind in ("research", "repositories"):
            page2 = self.result[kind]["page2"]
            self.assertIn("Showing 13 to 24.", page2["count"])
            self.assertTrue(page2["pageStatus"].startswith("Page 2 of"))
            self.assertFalse(page2["prevDisabled"])
            self.assertEqual(self.result[kind]["initial"]["count"], self.result[kind]["backToPage1"]["count"])

    def test_no_match_shows_empty_state_and_reset_restores_everything(self):
        for kind in ("research", "repositories"):
            empty = self.result[kind]["noMatch"]
            self.assertFalse(empty["emptyHidden"])
            self.assertTrue(empty["pagerHidden"])
            self.assertTrue(empty["cardsHidden"])
            self.assertIn("zzzzqqqq", empty["filters"])
            self.assertIn("0 of", empty["count"])
            self.assertFalse(empty["resetDisabled"])
            after = self.result[kind]["afterReset"]
            self.assertTrue(after["emptyHidden"])
            self.assertEqual(self.result[kind]["initial"]["count"], after["count"])
            self.assertEqual("", self.result[kind]["searchAfterReset"])
            self.assertEqual("#search", after["focus"])

    def test_page_size_filter_reset_and_table_toggle(self):
        for kind in ("research", "repositories"):
            self.assertEqual(24, self.result[kind]["size24"]["cards"])
            self.assertTrue(self.result[kind]["filtered"]["filters"].startswith("Active filters."))
            self.assertEqual("", self.result[kind]["filterAfterReset"])
            self.assertEqual("No filters are active.", self.result[kind]["afterResetButton"]["filters"])
            self.assertFalse(self.result[kind]["table"]["tableHidden"])
            self.assertTrue(self.result[kind]["table"]["cardsHidden"])
            self.assertEqual("true", self.result[kind]["togglePressed"])

    def test_directness_filter_matches_the_existing_values(self):
        self.assertEqual(self.result["pure"]["d3expected"], self.result["pure"]["d3count"])
        values = [o["value"] for o in self.result["research"]["options"]["filter"]]
        self.assertEqual(["", "D3", "D2", "D1", "D0", "unappraised"], values)
        texts = [o["text"] for o in self.result["research"]["options"]["filter"]]
        self.assertIn("Target-like", texts)

    def test_family_labels_replace_raw_codes_in_the_dropdown(self):
        theme = self.result["research"]["options"]["theme"]
        labels = {row["family"]: row["familyLabel"] for row in self.research}
        self.assertEqual(len(labels) + 1, len(theme))
        for option in theme[1:]:
            self.assertEqual(labels[option["value"]], htmllib.unescape(option["text"]))

    def test_recorded_order_is_unchanged_and_search_cannot_promote(self):
        pure = self.result["pure"]
        self.assertTrue(pure["untouched"])
        self.assertEqual(pure["total"], pure["everythingLength"])
        self.assertEqual(pure["expectedFirstIds"], pure["recordedOrderIds"])
        self.assertTrue(pure["subsequence"])
        self.assertGreater(pure["matchedLength"], 0)

    def test_null_grades_stay_unknown_and_automated_checks_are_labeled(self):
        pure = self.result["pure"]
        self.assertGreater(pure["automatedCount"], 0)
        self.assertTrue(pure["nullGradesStayNull"])
        self.assertEqual("Abstract relevance check, awaiting appraisal", pure["automatedDepth"])
        self.assertEqual(["README relevance check, awaiting appraisal", "Portable record: identity and provenance only",
                          "README screened against a pinned revision"], pure["repoLabels"])
        html = self.result["research"]["automatedHtml"]
        self.assertIn("Not graded yet", html)
        self.assertNotIn("0 / 3", html)
        self.assertIn("awaiting appraisal", self.result["repositories"]["automatedHtml"])
        self.assertIn("Unvetted third-party repository", self.result["repositories"]["automatedHtml"])

    def test_research_cards_say_the_date_is_not_recorded(self):
        html = self.result["research"]["cardsHtml"]
        self.assertIn("Publication or review date", html)
        self.assertIn("Not recorded", html)
        self.assertIn("Open original source", html)

    def test_repository_cards_distinguish_snapshot_review_and_star_dates(self):
        html = self.result["repositories"]["cardsHtml"]
        self.assertIn("Source snapshot", html)
        self.assertIn("A metadata or README screen is not a full appraisal.", html)
        self.assertIn("Observed", html)

    def test_primary_card_text_hides_ids_and_commits(self):
        for kind, rows in (("research", self.research), ("repositories", self.repositories)):
            html = self.result[kind]["cardsHtml"]
            primary = re.sub(r'<details class="reference">.*?</details>', "", html, flags=re.S)
            visible_text = re.sub(r"<[^>]+>", " ", primary)
            shown = [row for row in rows if row.get("snapshot_commit") and row["snapshot_commit"] in html]
            if kind == "repositories":
                self.assertTrue(shown)
            for row in shown:
                self.assertNotIn(row["snapshot_commit"][:8], primary)
            self.assertNotRegex(visible_text, r"\bR-\d{3}\b|\bCI-\d{3}\b")
            self.assertEqual(12, html.count('<details class="reference">'))

    def test_load_failure_path_is_visible(self):
        failed = self.result["researchFail"]["initial"]
        self.assertFalse(failed["loadErrorHidden"])
        self.assertEqual("The catalog could not load.", failed["count"])

    def test_page_boundaries(self):
        pure = self.result["pure"]
        self.assertEqual({"page": 1, "pages": 42, "size": 12, "start": 1, "end": 12, "hasPrev": False, "hasNext": True}, pure["p1"])
        self.assertEqual({"page": 1, "pages": 1, "size": 12, "start": 0, "end": 0, "hasPrev": False, "hasNext": False}, pure["p0"])
        self.assertEqual(3, pure["pClamp"]["page"])
        self.assertEqual(12, pure["pBadSize"]["size"])
        self.assertFalse(pure["pLast"]["hasNext"])
        self.assertIn("37 of 500 research records match. Showing 13 to 24.", pure["count"])
        self.assertEqual("0 of 500 research records match. Showing none.", pure["zeroCount"])

    def test_chart_titles_link_inside_the_site_and_keep_the_source_link(self):
        charts = self.result["charts"]
        self.assertIn(f'href="detail.html?type=research&amp;id={charts["researchId"]}"', charts["researchPrimary"])
        self.assertIn("Open original source", charts["researchPrimary"])
        self.assertIn("Review priority", charts["researchPrimary"])
        self.assertIn("tied entries share a number", charts["researchPrimary"])
        self.assertIn(f'href="detail.html?type=repositories&amp;id={charts["repoId"]}"', charts["repoPrimary"])
        if charts["repoCommit"]:
            self.assertNotIn(charts["repoCommit"][:8], charts["repoPrimary"])
            self.assertIn(charts["repoCommit"], charts["repoReference"])
        self.assertEqual(0, charts["noneLength"])
        self.assertEqual(charts["entriesLength"], charts["allLength"])
        self.assertTrue(charts["positionsKept"])
        self.assertEqual(["NEW", "UP 2", "DOWN 3", "UNCHANGED"], charts["movement"])

    def test_research_detail_page_has_back_link_next_action_and_reference(self):
        html = self.result["detailResearch"]
        self.assertIn('href="research.html"', html)
        self.assertIn("What to do next", html)
        self.assertIn("Open original source", html)
        self.assertIn("not recorded", html)
        primary, _, reference = html.partition('<details class="reference">')
        self.assertNotIn("MSR-WORK", primary)
        self.assertIn("MSR-WORK", reference)
        self.assertIn("<code>012</code>", reference)

    def test_automated_research_detail_does_not_claim_a_grade(self):
        html = self.result["detailAutomated"]
        self.assertIn("awaiting appraisal", html)
        self.assertIn("Not appraised", html)
        self.assertNotIn("0 / 3", html)

    def test_repository_detail_page_labels_mechanisms_and_hides_pins(self):
        html = self.result["detailRepo"]
        self.assertIn('href="repositories.html"', html)
        self.assertIn("Human Authority", html)
        primary, _, reference = html.partition('<details class="reference">')
        row = next(r for r in self.repositories if r["id"] == "R-242")
        self.assertNotIn(row["snapshot_commit"], primary)
        self.assertIn(row["snapshot_commit"], reference)
        self.assertIn("Source snapshot", primary)

    def test_missing_and_bad_links_point_to_the_catalogs(self):
        for key in ("detailMissing", "detailBad"):
            html = self.result[key]
            self.assertIn('href="research.html"', html)
            self.assertIn('href="repositories.html"', html)
            self.assertNotIn("Trail Map", html)
        self.assertIn("This profile is missing.", self.result["detailMissing"])

    def test_home_edition_text_is_labeled_and_failure_is_empty(self):
        self.assertIn("Latest edition: 2026-11-02.", self.result["homeText"])
        self.assertIn("not the freshness", self.result["homeText"])
        self.assertEqual("", self.result["homeBad"])


if __name__ == "__main__":
    unittest.main()
