// Per-region configuration for the AI Infrastructure Monitor — EUROPE.
// The shared engine (../app.js) reads `REGION_CONFIG`. This is the second reference
// implementation after the US; Europe launches LEAN — only the campus ledger + a curated
// overview are populated at first, and the capability manifest honestly marks the rest
// "not yet tracked" until ENTSO-E / Eurostat / curated feeds exist.
//
// Loaded before the engine (see <script src="config.js"> then <script src="../app.js"> in
// eu/index.html <head>), so REGION_CONFIG is defined when the engine runs.
// Keep this LEAN — region identity/config only; large arrays (the ledger, source ledger,
// time-series) live in eu/data/, never here.
const REGION_CONFIG = {
  id: "eu",
  brand: "AI Infrastructure Monitor — Europe",
  region: "Europe",
  repoUrl: "https://github.com/vijay-sachdeva/ai-infra",
  liveUrl: "https://vijay-sachdeva.github.io/ai-infra/eu",
  themeKey: "eu-ai-theme",
  geoLabel: "Country",   // the ledger's geo column shows ISO2 country codes, not US states
  // No Europe chat backend yet — the EU shell omits the chat UI entirely. Set a Worker URL
  // here (and add the chat markup/script to eu/index.html) to enable it later.
  chatEndpoint: null,

  // Capability manifest — which tabs/datasets Europe actually has verified data for. A key set
  // false makes the engine mark that nav tab "soon" and render an honest "not yet tracked"
  // placeholder instead of faking US-style parity. We flip a key to true only once a real,
  // sourced feed exists for it. (Missing key would default to enabled — so be explicit here.)
  capabilities: {
    overview: true,    // curated Europe intro + headline stats (static, sourced)
    buildout: true,    // hosts the European campus ledger (renderMegaProjects)
    grid:     false,   // ENTSO-E fetcher scaffolded; flip true once eu/data/grid.json publishes
    capital:  false,   // no Europe capex/deal dataset yet
    tokens:   false,   // no Europe compute/token dataset yet
    // card-level flags (informational + future [data-capability] gating):
    map:        false, // a Europe map (projection + topojson) is a follow-up
    projects:   true,
    queues:     false,
    rateImpacts:false,
    gridFeeds:  false
  },

  // Feeds hydrate() pulls from eu/data/<feed>.json (current.json is loaded separately as the
  // live headline layer). Add "grid"/"power_econ" here once their fetchers publish.
  feeds: ["projects", "sources"],
  feedMeta: { grid: "ENTSO-E Transparency", power_econ: "Eurostat prices" },

  // Operator monograms: ticker / company-name -> { brand, letter }. European builds are mostly
  // the same hyperscalers as the US plus European players; "other" falls back to a neutral mark.
  operators: {
    AMZN: { brand: "aws",       letter: "a" }, "Amazon": { brand: "aws", letter: "a" }, "AWS": { brand: "aws", letter: "a" },
    MSFT: { brand: "microsoft", letter: "M" }, "Microsoft": { brand: "microsoft", letter: "M" },
    GOOGL:{ brand: "google",    letter: "G" }, "Google": { brand: "google", letter: "G" }, "Alphabet": { brand: "google", letter: "G" },
    META: { brand: "meta",      letter: "M" }, "Meta": { brand: "meta", letter: "M" },
    ORCL: { brand: "oracle",    letter: "O" }, "Oracle": { brand: "oracle", letter: "O" },
    NVDA: { brand: "nvidia",    letter: "N" }, "Nvidia": { brand: "nvidia", letter: "N" }, "NVIDIA": { brand: "nvidia", letter: "N" },
    "Nscale":   { brand: "other", letter: "N" },
    "Nebius":   { brand: "nebius", letter: "N" },
    "Mistral":  { brand: "other", letter: "M" },
    "Equinix":  { brand: "other", letter: "E" },
    "Vantage":  { brand: "other", letter: "V" },
    "CyrusOne": { brand: "other", letter: "C" },
    "Iliad":    { brand: "other", letter: "I" },
    "OpenAI":   { brand: "other", letter: "O" }
  }
};
