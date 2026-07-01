# AI Infrastructure Monitor

Open, source-linked dashboards tracking the build-out of AI data-center infrastructure —
capacity, power, capital, and named campuses — **one region at a time**, served from a single
shared engine.

- **United States** — the mature, full-featured dashboard, in its own repo:
  [`us-ai-infra`](https://github.com/vijay-sachdeva/us-ai-infra) →
  <https://vijay-sachdeva.github.io/us-ai-infra/>
- **Europe** — a lean pilot in this repo: [`/eu/`](eu/) →
  <https://vijay-sachdeva.github.io/ai-infra/eu/>
- **India, LATAM, Africa** — planned, same template.

## Architecture — one engine, per-region data

The US dashboard was refactored into a reusable template. Every region is three thin layers
plus data, sharing one engine file:

```
ai-infra/
  app.js            ← the shared, region-agnostic ENGINE (copied from the US template).
                      Chart system, tab nav, theme, hydrate(), the storyboards, the ledger
                      renderer, capability gating. Reads REGION_CONFIG + DATA.
  index.html        ← umbrella landing (region switcher).
  eu/
    index.html      ← a thin per-region SHELL: <head>/SEO, the static tab skeleton + region
                      copy, an inline minimal DATA, then <script src="config.js"> +
                      <script src="../app.js">.
    config.js       ← REGION_CONFIG: brand, URLs, theme key, operator monograms, feeds, and
                      the CAPABILITY MANIFEST (which tabs have verified data).
    data/           ← per-region feeds + the projects ledger, same schema as the US.
  scripts/eu/       ← per-region data fetchers (ENTSO-E, Eurostat) + the daily news refresh.
```

### Capability manifest — launch lean, grow honestly

`config.js` declares `capabilities: { overview, buildout, grid, capital, tokens, … }`. A tab whose
capability is `false` renders an honest **"not yet tracked — contributions welcome"** placeholder
(and a "soon" nav badge) instead of faking parity with the more mature US dashboard. A region flips
a capability to `true` only once a real, sourced feed backs it. This is the anti-fabrication
mechanism: we omit, never invent, a region's missing data.

### No fabrication

Every figure is source-linked and provenance-tagged (`provenance` / `transformation` / `confidence`).
The Europe ledger was **adversarially re-verified** (each record's sources re-fetched by an
independent checker) before publication — see `eu/data/projects.json` → `verification`, and its
`caveats` + `known_gaps`.

## Adding a region

1. Copy `app.js` (kept in sync from the US template).
2. Add `<geo>/index.html` (shell + copy), `<geo>/config.js` (a lean capability manifest),
   and `<geo>/data/` (at least a `projects.json` ledger, same schema).
3. Add `scripts/<geo>/` fetchers for whatever public feeds the region has.
4. Enable only the capabilities you have verified data for.

## Deploy

GitHub Pages from `main` at the repo root. Each region lives at a subpath (`/eu/`, `/in/`, …).
`<geo>/index.html` loads the root `app.js` via `../app.js`; `hydrate()` fetches `data/*.json`
relative to the page. No build step.

## Data & licensing

Code is **MIT** (`LICENSE`); the compiled datasets are **CC BY 4.0** (`eu/data/LICENSE`).
Third-party sources cited per record remain under their own owners' terms.
