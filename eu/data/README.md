# Europe data — dictionary & provenance

All files are **CC BY 4.0** (see `LICENSE`). Suggested citation: *"AI Infrastructure Monitor —
Europe — data CC BY 4.0, vijay-sachdeva.github.io/ai-infra/eu."*

## `projects.json` — the campus & investment ledger (flagship)

Named European AI / hyperscaler data-center campuses, country-level capex programs, and one
EU-wide policy initiative. Same schema as the US ledger
([`us-ai-infra/schemas/projects.schema.json`](https://github.com/vijay-sachdeva/us-ai-infra/blob/main/schemas/projects.schema.json)).

Per-record fields: `id`, `name`, `operator`, `state` (ISO2 country code, or `EU`), `country_name`,
`location{lat,lon,precision}`, `capacity_mw` (may be `null`), `capacity_type`
(`it_critical_load` | `total_power` | `unspecified`), `status`
(`announced` | `planned` | `construction` | `operational`), `status_as_of`,
`power{generation,model}`, `note`, `provenance`, `transformation`, `confidence`, `revision`,
`record_type` (`campus` | `capex_program` | `policy_program`), and `sources[]` (each with a
verified `url`, `publisher`, `published`, `retrieved`, `supports_claim`).

**Verification.** Every record was adversarially re-verified by re-fetching its sources — see the
`verification` block in `projects.json`.

**Derived exports.** `projects.csv` (flat table) and `projects.geojson` (mapped points, records
with coordinates) are generated from `projects.json` by `scripts/eu/build_projects_exports.py` —
regenerate after any ledger edit. `projects.json` is the canonical source.

**Read the caveats.** The dataset carries a `caveats` array and a `known_gaps` array. In short:
- **Do not sum `capacity_mw`.** Only ~7 of 18 records disclose MW, and they mix ultimate campus
  targets, a wind-supply figure, and one IT-critical-load number. Most hyperscaler records are
  capex programs with `capacity_mw: null` (the figure is investment, in the `note`).
- **`record_count` ≠ data centers.** Some records bundle multiple sites; one is an EU-wide program.
- **Known gap:** Ireland/Dublin is the #1 addition for the next version.

## `sources.json`

Shared source ledger for `linkifySources()`. Seeded empty for the pilot (per-record sources live
inline in `projects.json`); grows as grid/capital feeds are added.

## `current.json`

The live headline layer (`lastUpdated`, `topStory`, `feed`, `kpis`), edited by
`scripts/eu/daily_refresh.py`. `hydrate()` overlays it onto the inline `DATA`.

## `power_econ.json` (generated)

European industrial electricity prices from **Eurostat** `nrg_pc_205` (non-household, band
500–1,999 MWh/yr, all taxes, EUR/kWh), via `scripts/eu/fetch_eurostat.py`. Present as a demonstrated
feed; not yet surfaced in the UI (the prices/grid capability is gated off until wired).

## `grid.json` (generated, requires a token)

European actual electricity load from the **ENTSO-E Transparency Platform**, via
`scripts/eu/fetch_entsoe.py` (needs `ENTSOE_API_TOKEN`). Not produced until the token is set; the
Grid tab shows the "not yet tracked" placeholder until then.
