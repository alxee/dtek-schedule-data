"""Fetch DTEK KREM schedule (all groups) with headless Chromium and write schedule.json.
Only rewrites the file when the schedule itself changed (timestamps are ignored)."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE = "https://www.dtek-krem.com.ua/ua/shutdowns"
OUT = Path("schedule.json")
VOLATILE = {"update", "updateFact"}
dec = json.JSONDecoder()


def extract(html: str, name: str) -> dict:
    key = f"DisconSchedule.{name} = "
    i = html.find(key)
    if i < 0:
        raise RuntimeError(f"DisconSchedule.{name} not found (challenge page?): {html[:200]!r}")
    return dec.raw_decode(html, i + len(key))[0]


def strip(d: dict) -> dict:
    return {k: strip(v) if isinstance(v, dict) else v for k, v in d.items() if k not in VOLATILE}


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(locale="uk-UA", timezone_id="Europe/Kyiv")
        page = ctx.new_page()
        page.goto(PAGE, wait_until="networkidle", timeout=90_000)
        html = page.content()
        browser.close()
    new = {"preset": extract(html, "preset"), "fact": extract(html, "fact")}
    try:
        old = json.loads(OUT.read_text())
    except (FileNotFoundError, ValueError):
        old = None
    if old and strip(old) == strip(new):
        print("unchanged")
        return 0
    OUT.write_text(json.dumps(new, ensure_ascii=False, separators=(",", ":")))
    print("updated", OUT.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
