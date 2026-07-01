#!/usr/bin/env python3
"""Daily news refresh for the AI Infrastructure Monitor — Europe pilot.

Asks Claude (Anthropic API, with web search) to identify fresh EUROPEAN AI
data-center news and update two fields in **eu/data/current.json**:
  * lastUpdated:  YYYY-MM-DD
  * topStory:     { date, text, src, url }

Mirrors the US scripts/daily_refresh.py (edits a small JSON file, never the HTML
shell) but scopes the search to Europe. Safe: validates the model's JSON shape +
date; aborts on a malformed topStory rather than writing garbage.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# eu/data/current.json relative to this file (scripts/eu/ -> ../../eu/data/)
CURRENT_JSON = Path(__file__).resolve().parent.parent.parent / "eu" / "data" / "current.json"

MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 8192
WEB_SEARCH_MAX_USES = 5
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOP_STORY_KEYS = ("date", "text", "src", "url")


def build_prompt(last_updated, top_story_json, today_iso):
    return f"""You are doing the daily news refresh for the AI Infrastructure Monitor - EUROPE dashboard
at https://vijay-sachdeva.github.io/ai-infra/eu/.

GOAL: identify significant EUROPEAN AI data-center news from the past ~24-72 hours and decide whether to
update two fields: lastUpdated (YYYY-MM-DD) and topStory ({{ date, text, src, url }}).

SCOPE - EUROPE ONLY (EU-27 + UK + Norway/Iceland/Switzerland). Ignore US/Asia-only news unless it has a
direct, material European data-center hook.

ALWAYS-SIGNIFICANT SUBJECTS: hyperscaler EU builds (Microsoft, AWS/Amazon, Google, Meta, Oracle), EU AI
gigafactories / InvestAI, European neo-clouds (Nebius, Nscale, Mistral, CoreWeave EU), large campus
announcements (>100 MW or >EUR 500M), national grid/interconnection news affecting AI load, and EU/national
policy (sovereignty, permitting, energy).

CONSTRAINTS: prefer primary sources (company press/IR, EU/national government, ENTSO-E, Eurostat) and credible
trade press (Data Center Dynamics, Reuters, Bloomberg, Euractiv). Avoid speculation and generic AI hype.

ROTATE FOR FRESHNESS: if you find ANY material European AI-infra item more recent than the current topStory's
date, swap to the freshest such item (recency beats magnitude). Keep the current story (topStory: null) ONLY
when nothing more recent exists. DO NOT FABRICATE - every swap must be a real item with a working source URL.

TODAY (UTC): {today_iso}
CURRENT lastUpdated: {last_updated}
CURRENT topStory (JSON):
```
{top_story_json}
```

OUTPUT: return STRICTLY one JSON object (no fences, no commentary). To swap in a fresh story:
{{"lastUpdated":"{today_iso}","topStory":{{"date":"Mon DD, YYYY","text":"1-2 factual sentences","src":"Publisher","url":"https://..."}},"summary":"one-line description"}}
On a dead news day: {{"lastUpdated":"{today_iso}","topStory":null,"summary":"Date bump only"}}

Hard rules: valid JSON (escape quotes, no trailing commas, no literal newlines in strings); "date" is the real
publication date; "url" is a real link found via web_search. Begin.
"""


def _date_bump_only(today_iso, reason):
    return {"lastUpdated": today_iso, "topStory": None, "summary": f"Date bump only ({reason})"}


def _extract_json(text):
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for pat in (r'```json\s*(\{[\s\S]*?\})\s*```', r'```\s*(\{[\s\S]*?\})\s*```'):
        for m in re.finditer(pat, text):
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
    depth, start = 0, -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        p = json.loads(text[start:i + 1])
                        if isinstance(p, dict) and "lastUpdated" in p:
                            return p
                    except json.JSONDecodeError:
                        pass
    return None


def call_claude(prompt, today_iso):
    from anthropic import Anthropic  # lazy import
    client = Anthropic()
    resp = client.messages.create(
        model=MODEL, max_tokens=MAX_TOKENS,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": WEB_SEARCH_MAX_USES}],
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"[eu-refresh] stop_reason={resp.stop_reason} blocks={len(resp.content)}")
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if not text:
        return _date_bump_only(today_iso, f"no text; stop_reason={resp.stop_reason}")
    parsed = _extract_json(text)
    if parsed is None:
        print("[eu-refresh] JSON extraction failed; date-bump only.", file=sys.stderr)
        return _date_bump_only(today_iso, "JSON extraction failed")
    return parsed


def main():
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not CURRENT_JSON.exists():
        print(f"[eu-refresh] ERROR: {CURRENT_JSON} not found", file=sys.stderr)
        return 1
    data = json.loads(CURRENT_JSON.read_text(encoding="utf-8"))
    last_updated = data.get("lastUpdated")
    if last_updated == today_iso:
        print("[eu-refresh] already updated today — exiting cleanly")
        return 0
    top = data.get("topStory") or {}
    prompt = build_prompt(last_updated, json.dumps(top, ensure_ascii=False, indent=2), today_iso)
    try:
        edits = call_claude(prompt, today_iso)
    except Exception as e:
        print(f"[eu-refresh] ERROR calling Claude: {e}", file=sys.stderr)
        return 1

    new_date = edits.get("lastUpdated") or today_iso
    if not DATE_RE.match(str(new_date)):
        new_date = today_iso
    data["lastUpdated"] = new_date

    new_top = edits.get("topStory")
    if new_top is not None:
        if not (isinstance(new_top, dict) and all(k in new_top and isinstance(new_top[k], str) and new_top[k].strip()
                                                  for k in TOP_STORY_KEYS)):
            print("[eu-refresh] ABORT: malformed topStory — not writing.", file=sys.stderr)
            return 1
        if not str(new_top["url"]).startswith("http"):
            print("[eu-refresh] ABORT: topStory.url is not a URL — not writing.", file=sys.stderr)
            return 1
        data["topStory"] = {k: new_top[k] for k in TOP_STORY_KEYS}

    CURRENT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[eu-refresh] OK: {edits.get('summary', '(no summary)')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
