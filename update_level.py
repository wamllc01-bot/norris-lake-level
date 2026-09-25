#!/usr/bin/env python3
"""
Writes norris-level.json with the current Norris Lake elevation.

Primary source: TVA's own lake-levels page (https://www.tva.com/environment/lake-levels/norris),
read with a headless browser because TVA fills the numbers in with JavaScript.
Fallback: https://www.norrislakenews.com/Level.asp (plain HTML, same TVA reading).

Runs daily via GitHub Actions (.github/workflows/lake-level.yml).
"""
import json, re, sys, datetime, html, urllib.request

FULL_POOL = 1020.0
OUT_FILE = "norris-level.json"
TVA_URL = "https://www.tva.com/environment/lake-levels/norris"
FALLBACK_URL = "https://www.norrislakenews.com/Level.asp"
UA = "Mozilla/5.0 (compatible; LakeNorrisChalets level bot; +https://lakenorrischalets.com)"
SANE = (940.0, 1040.0)


def from_tva():
    """Load TVA's Norris page in headless Chromium and pull the observed elevation."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=UA)
        page.goto(TVA_URL, wait_until="networkidle", timeout=60000)
        # Give the data script a moment; wait until a Norris-range number shows up in the text.
        page.wait_for_function(
            "() => /\\b(9[4-9]\\d|10[0-3]\\d)\\.\\d/.test(document.body.innerText)", timeout=30000)
        text = re.sub(r"\s+", " ", page.inner_text("body"))
        browser.close()
    print("TVA page text (first 1500 chars):", text[:1500], file=sys.stderr)

    # Prefer a number that sits near the word "Observed"; otherwise the first sane number.
    m = (re.search(r"[Oo]bserved[^0-9]{0,120}\b((?:9[4-9]\d|10[0-3]\d)\.\d+)", text)
         or re.search(r"\b((?:9[4-9]\d|10[0-3]\d)\.\d+)\b", text))
    if not m:
        raise RuntimeError("No Norris-range elevation found on TVA page")
    ft = float(m.group(1))
    # Try to find a date/time near the reading.
    d = re.search(r"(\d{1,2}/\d{1,2}/\d{4})(?:[ ,]+(\d{1,2}:\d{2}\s*[AP]?M?))?", text)
    if d:
        observed = datetime.datetime.strptime(d.group(1), "%m/%d/%Y").date().isoformat()
        observed_text = d.group(1) + (f" {d.group(2)}" if d.group(2) else "")
    else:
        observed = datetime.date.today().isoformat(); observed_text = observed
    return ft, observed, observed_text, "TVA"


def from_norrislakenews():
    req = urllib.request.Request(FALLBACK_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = html.unescape(r.read().decode("utf-8", "ignore"))
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))
    m = re.search(r"WATER LEVEL\s*([\d,]+\.\d+)\s*Feet MSL", text, re.I)
    if not m:
        raise RuntimeError("Could not find 'WATER LEVEL ... Feet MSL'")
    ft = float(m.group(1).replace(",", ""))
    d = re.search(r"([A-Z][a-z]+day,\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4})(?:\s+(\d{1,2}:\d{2}:\d{2}\s*[AP]M))?",
                  text[m.end():m.end() + 200])
    if d:
        observed = datetime.datetime.strptime(d.group(1), "%A, %B %d, %Y").date().isoformat()
        observed_text = d.group(1) + (f" {d.group(2)}" if d.group(2) else "")
    else:
        observed = datetime.date.today().isoformat(); observed_text = observed
    return ft, observed, observed_text, "norrislakenews.com"


def main():
    result = None
    for getter in (from_tva, from_norrislakenews):
        try:
            result = getter()
            if SANE[0] <= result[0] <= SANE[1]:
                break
            print(f"{getter.__name__}: {result[0]} out of range", file=sys.stderr)
            result = None
        except Exception as e:
            print(f"{getter.__name__} failed: {e}", file=sys.stderr)

    if not result:
        try:  # keep the last good reading rather than publishing nothing
            prev = json.load(open(OUT_FILE)); prev["stale"] = True
            json.dump(prev, open(OUT_FILE, "w"), indent=2)
        except FileNotFoundError:
            pass
        sys.exit(1)

    ft, date, when, src = result
    data = {
        "lake": "Norris",
        "elevation": round(ft, 2),
        "date": date,
        "observed": when,
        "full_pool": FULL_POOL,
        "below_full_pool": round(FULL_POOL - ft, 2),
        "source": src,
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    json.dump(data, open(OUT_FILE, "w"), indent=2)
    print(json.dumps(data))


if __name__ == "__main__":
    main()
