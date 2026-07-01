#!/usr/bin/env python3
"""Fetch European industrial electricity prices from Eurostat -> eu/data/power_econ.json.

Source: Eurostat dataset nrg_pc_205 (electricity prices for non-household consumers),
via the public dissemination API (JSON-stat 2.0, no API key required).
Docs: https://ec.europa.eu/eurostat/web/energy/database

This is the Europe analogue of the US scripts/fetch_power_econ.py. It pulls the most
recent available period's price (EUR per kWh, all taxes included) for a mid-size
industrial consumption band across the major European AI data-center markets, so the
dashboard can eventually show a comparable "what does power cost" panel.

Stdlib only (urllib + json). Run: python scripts/eu/fetch_eurostat.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "eu" / "data" / "power_econ.json"

# nrg_pc_205 filters: band IB = 500 MWh–2,000 MWh/yr (mid industrial), all-taxes price in EUR/kWh.
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_205"
PARAMS = {
    "format": "JSON",
    "lang": "EN",
    "freq": "S",             # semi-annual (the dataset's only frequency)
    "siec": "E7000",         # electricity (Standard International Energy Classification)
    "unit": "KWH",           # euro per kWh
    "nrg_cons": "MWH500-1999",  # mid-size industrial band (500-1,999 MWh/yr)
    "tax": "I_TAX",          # all taxes and levies included
    "currency": "EUR",
}
# Focus markets (ISO2 -> label). Eurostat uses EL for Greece, UK for United Kingdom.
MARKETS = {
    "DE": "Germany", "FR": "France", "IE": "Ireland", "NL": "Netherlands",
    "ES": "Spain", "FI": "Finland", "SE": "Sweden", "DK": "Denmark",
    "IT": "Italy", "PT": "Portugal", "BE": "Belgium", "NO": "Norway",
}


def _decode_jsonstat(js):
    """Decode a JSON-stat 2.0 dataset into {(geo, time): value} using stride math."""
    ids = js["id"]
    size = js["size"]
    dims = {}
    for d in ids:
        idx = js["dimension"][d]["category"]["index"]
        if isinstance(idx, dict):
            dims[d] = idx  # {code: pos}
        else:
            dims[d] = {code: i for i, code in enumerate(idx)}
    # strides: last dim stride 1, moving left multiply by size
    strides = [1] * len(ids)
    for i in range(len(ids) - 2, -1, -1):
        strides[i] = strides[i + 1] * size[i + 1]
    values = js["value"]
    if isinstance(values, list):
        values = {i: v for i, v in enumerate(values) if v is not None}
    else:
        values = {int(k): v for k, v in values.items()}
    geo_pos = dims["geo"]
    time_pos = dims["time"]
    time_i = ids.index("time")
    geo_i = ids.index("geo")
    out = {}
    for gcode, gp in geo_pos.items():
        for tcode, tp in time_pos.items():
            flat = 0
            for i, d in enumerate(ids):
                if d == "geo":
                    flat += gp * strides[i]
                elif d == "time":
                    flat += tp * strides[i]
                # all other dims are single-valued (pinned by filters) -> pos 0
            if flat in values:
                out[(gcode, tcode)] = values[flat]
    return out


def main():
    qs = "&".join(f"{k}={v}" for k, v in PARAMS.items())
    qs += "".join(f"&geo={g}" for g in MARKETS)
    url = f"{BASE}?{qs}"
    print(f"[eurostat] GET {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            js = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[eurostat] ERROR fetching: {e}", file=sys.stderr)
        return 1
    try:
        decoded = _decode_jsonstat(js)
    except Exception as e:
        print(f"[eurostat] ERROR decoding JSON-stat: {e}", file=sys.stderr)
        return 1

    # latest period per country
    rows = []
    latest_period = None
    for geo, name in MARKETS.items():
        periods = sorted([t for (g, t) in decoded if g == geo])
        if not periods:
            continue
        t = periods[-1]
        latest_period = max(latest_period or t, t)
        rows.append({"country": geo, "name": name, "price_eur_kwh": round(decoded[(geo, t)], 4), "period": t})

    out = {
        "name": "European industrial electricity prices",
        "source": "Eurostat nrg_pc_205 (non-household, band 500-1999 MWh/yr, all taxes, EUR/kWh)",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/",
        "unit": "EUR/kWh",
        "period": latest_period,
        "rows": sorted(rows, key=lambda r: r["price_eur_kwh"], reverse=True),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[eurostat] wrote {OUT} — {len(rows)} countries, period {latest_period}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
