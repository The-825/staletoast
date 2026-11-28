# Added-component retained-pool routing screen (2026-11-27)

Generated from [staletoast-added-component-pool-screen-2026-11-27.json](staletoast-added-component-pool-screen-2026-11-27.json) by `python scripts/screen_added_components.py`.

**Kind:** `routing-proposal` (read-only routing proposal; `scope_map_status_unchanged = true`).

**Authority:** evidence-only; deterministic term screen over the retained pool. Does not promote components to established, assign grades, release held sources, or authorize adoption.

## Pool coverage summary

- Retained expansion pool records inspected: **1083**
- Held records excluded under disposition boundaries: **41**
- Active retained records screened: **1042**
- Distinct active candidate sources matching at least one component: **91**
- Total component routing assignments across those candidates: **94** (a source may match more than one component)
- Held-source term matches kept excluded: **2** (out of 41 held records)

| Component | Active matches | Research | Repositories | Held matches kept excluded | Thin (<10 active)? |
|---|---:|---:|---:|---:|---|
| `security-and-containment` | 24 | 4 | 20 | 0 | no (appraise existing pool first) |
| `deliberation-and-dissent` | 6 | 2 | 4 | 0 | yes (eligible for targeted discovery) |
| `learning-from-operation` | 11 | 4 | 7 | 0 | no (appraise existing pool first) |
| `orchestration-and-automation` | 53 | 8 | 45 | 2 | no (appraise existing pool first) |

## Governance boundaries preserved

1. Every candidate keeps `grade: null`, `adoption: not adopted`, and `hot100_selection: not selected`.
2. All 41 held sources in `docs/staletoast-source-dispositions.json` remain excluded from `candidates`, including offensive or evasion-focused security repositories.
3. `docs/staletoast-scope-map.json` keeps all four November 27 components at `added-unscreened` until human appraisal compares primary sources against each component's baseline question.
4. No catalog export, frozen snapshot, or Hot 100 edition is modified by this routing proposal.
