#!/usr/bin/env python3
"""
Writes norris-level.json with the current Norris Lake elevation.
Source: https://www.norrislakenews.com/Level.asp (Lakes Online), which
publishes the TVA reading as plain text.
Runs daily via GitHub Actions (.github/workflows/lake-level.yml).
"""
import json, re, sys, datetime, html, urllib.request

SOURCE = "https://www.norrislakenews.com/Level.asp"
FULL_POOL = 1020.0
OUT_FILE = "norris-level.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; LakeNorrisChalets level bot; +https://lakenorrischalets.com)"}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def get_norris_elevation():
    """Return (elevation_ft, observed_date 'YYYY-MM-DD', observed_text)."""
    page = html.unescape(fetch(SOURCE))
    text = re.sub(r"<[^>]+>", " ", page)          # strip tags
    text = re.sub(r"\s+", " ", text)

    # e.g. "WATER LEVEL 1,015.17 Feet MSL Saturday, July 25, 2026 6:00:00 PM"
    m = re.search(r"WATER LEVEL\s*([\d,]+\.\d+)\s*Feet MSL", text, re.I)
    if not m:
        raise RuntimeError("Could not find 'WATER LEVEL ... Feet MSL' on the page")
    elevation = float(m.group(1).replace(",", ""))
    if not 940 <= elevation <= 1040:
        raise RuntimeError(f"Elevation {elevation} is outside a sane range for Norris")

    d = re.search(r"([A-Z][a-z]+day,\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4})(?:\s+(\d{1,2}:\d{2}:\d{2}\s*[AP]M))?", text[m.end():m.end()+200])
    if d:
        observed = datetime.datetime.strptime(d.group(1), "%A, %B %d, %Y").date().isoformat()
        observed_text = d.group(1) + (f" {d.group(2)}" if d.group(2) else "")
    else:
        observed = datetime.date.today().isoformat()
        observed_text = observed
    return elevation, observed, observed_text


def main():
    try:
        ft, date, when = get_norris_elevation()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        try:  # keep the last good reading rather than publishing nothing
            prev = json.load(open(OUT_FILE))
            prev["stale"] = True
            json.dump(prev, open(OUT_FILE, "w"), indent=2)
        except FileNotFoundError:
            pass
        sys.exit(1)

    data = {
        "lake": "Norris",
        "elevation": round(ft, 2),
        "date": date,
        "observed": when,
        "full_pool": FULL_POOL,
        "below_full_pool": round(FULL_POOL - ft, 2),
        "source": SOURCE,
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    json.dump(data, open(OUT_FILE, "w"), indent=2)
    print(json.dumps(data))


if __name__ == "__main__":
    main()
