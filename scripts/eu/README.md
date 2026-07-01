# Europe data pipeline

| Script | Output | Needs | Notes |
|---|---|---|---|
| `fetch_eurostat.py` | `eu/data/power_econ.json` | — (stdlib) | Eurostat `nrg_pc_205` industrial electricity prices (EUR/kWh). Works today. |
| `fetch_entsoe.py` | `eu/data/grid.json` | `ENTSOE_API_TOKEN` | ENTSO-E actual total load (MW) per country. Skips cleanly if no token. |
| `daily_refresh.py` | `eu/data/current.json` | `ANTHROPIC_API_KEY` | Claude web-search news refresh, scoped to European AI-infra news. |

Run from the repo root, e.g. `python scripts/eu/fetch_eurostat.py`.

To light up the **Grid & power** tab: set `ENTSOE_API_TOKEN`, run `fetch_entsoe.py`, add `"grid"`
to `feeds` in `eu/config.js`, and flip `capabilities.grid` to `true`. Until then the tab shows the
honest "not yet tracked" placeholder.
