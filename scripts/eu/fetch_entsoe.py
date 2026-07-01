#!/usr/bin/env python3
"""Fetch European electricity load from the ENTSO-E Transparency Platform -> eu/data/grid.json.

Source: ENTSO-E Transparency Platform REST API (Actual Total Load, documentType A65 /
processType A16). Requires a free security token in the ENTSOE_API_TOKEN env var
(register at https://transparency.entsoe.eu/ then request API access).
API guide: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html

This is the Europe analogue of the US scripts/fetch_grid.py. It pulls the most recent
actual total load (MW) for the major European AI data-center markets, so the dashboard's
"Grid & power" tab can eventually show real demand context. Until this publishes a
grid.json AND capabilities.grid is flipped to true in eu/config.js, the Grid tab renders
the honest "not yet tracked" placeholder.

Stdlib only (urllib + xml.etree). Run: ENTSOE_API_TOKEN=xxxx python scripts/eu/fetch_entsoe.py

NOTE: the EIC bidding-zone codes below are the commonly-documented ones; verify against the
ENTSO-E EIC list if a country returns no data (some countries have multiple zones).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "eu" / "data" / "grid.json"
BASE = "https://web-api.tps.entsoe.eu/api"

# ISO2 -> (label, EIC bidding-zone/control-area domain)
ZONES = {
    "DE": ("Germany (DE-LU)", "10Y1001A1001A82H"),
    "FR": ("France", "10YFR-RTE------C"),
    "IE": ("Ireland (SEM)", "10Y1001A1001A59C"),
    "NL": ("Netherlands", "10YNL----------L"),
    "ES": ("Spain", "10YES-REE------0"),
    "FI": ("Finland", "10YFI-1--------U"),
    "SE": ("Sweden", "10YSE-1--------K"),
    "BE": ("Belgium", "10YBE----------2"),
    "IT": ("Italy", "10YIT-GRTN-----B"),
    "NO": ("Norway", "10YNO-0--------C"),
    "DK": ("Denmark (DK1)", "10YDK-1--------W"),
    "PT": ("Portugal", "10YPT-REN------W"),
}


def _fmt(dt):
    return dt.strftime("%Y%m%d%H%M")


def fetch_load(token, domain):
    now = datetime.now(timezone.utc)
    params = {
        "securityToken": token,
        "documentType": "A65",       # System total load
        "processType": "A16",        # Realised
        "outBiddingZone_Domain": domain,
        "periodStart": _fmt(now - timedelta(hours=26)),
        "periodEnd": _fmt(now),
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as r:
        xml = r.read().decode("utf-8")
    # strip default namespace for easy tag matching
    root = ET.fromstring(xml)
    ns = {"": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    def find_all(tag):
        return root.iter("{%s}%s" % (ns[""], tag)) if ns else root.iter(tag)
    points = []
    for pt in find_all("Point"):
        qs = pt.find("{%s}quantity" % ns[""]) if ns else pt.find("quantity")
        if qs is not None and qs.text:
            points.append(float(qs.text))
    if not points:
        return None
    return {"latest_mw": round(points[-1]), "peak_mw": round(max(points)), "points": len(points)}


def main():
    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        print("[entsoe] ENTSOE_API_TOKEN not set — skipping (grid capability stays gated off).",
              file=sys.stderr)
        return 0  # not an error: the pilot launches without grid data
    rows = []
    for iso, (label, domain) in ZONES.items():
        try:
            data = fetch_load(token, domain)
        except Exception as e:
            print(f"[entsoe] {iso} ({domain}) failed: {e}", file=sys.stderr)
            continue
        if data:
            rows.append({"country": iso, "name": label, **data})
            print(f"[entsoe] {iso}: latest {data['latest_mw']} MW, peak {data['peak_mw']} MW")
    if not rows:
        print("[entsoe] no data returned for any zone — not writing.", file=sys.stderr)
        return 1
    out = {
        "name": "European electricity load (actual total)",
        "source": "ENTSO-E Transparency Platform (Actual Total Load, A65/A16)",
        "source_url": "https://transparency.entsoe.eu/",
        "unit": "MW",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": sorted(rows, key=lambda r: r["peak_mw"], reverse=True),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[entsoe] wrote {OUT} — {len(rows)} zones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
