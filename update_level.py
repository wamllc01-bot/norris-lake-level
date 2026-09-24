#!/usr/bin/env python3
"""
Writes norris-level.json with the current Norris Lake elevation.
Runs daily via GitHub Actions (see .github/workflows/lake-level.yml).

If you already have a script that pulls the Norris elevation from TVA,
paste its fetch logic into get_norris_elevation() below and delete the
default attempt. The rest of this file does not need to change.
"""
import json, re, sys, datetime, urllib.request

FULL_POOL = 1020.0
OUT_FILE = "norris-level.json"
UA = {"User-Agent": "Mozilla/5.0 (LakeNorrisChalets level bot)"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def get_norris_elevation():
    """Return (elevation_ft: float, observed_date: 'YYYY-MM-DD')."""
    # ---- PASTE YOUR EXISTING TVA FETCH HERE ------------------------------
    # It should end with:  return float(elevation), "YYYY-MM-DD"
    # ----------------------------------------------------------------------

    # Default attempt: pull TVA's Norris page and look for an observed
    # elevation in the plausible range for Norris (955–1035 ft).
    for url in (
        "https://www.tva.com/Environment/Lake-Levels/Norris/48-Hours",
        "https://www.tva.com/environment/lake-levels/norris",
    ):
        try:
            html = _get(url)
        except Exception as e:
            print(f"fetch failed {url}: {e}", file=sys.stderr)
            continue
        # Look for a number near the word "observed" first, then anywhere.
        for pattern in (r"[Oo]bserved[^0-9]{0,200}(9[5-9]\d\.\d|10[0-3]\d\.\d)",
                        r"\b(9[5-9]\d\.\d|10[0-3]\d\.\d)\b"):
            m = re.search(pattern, html)
            if m:
                return float(m.group(1)), datetime.date.today().isoformat()
    raise RuntimeError("Could not find a Norris elevation on TVA's site")


def main():
    try:
        ft, date = get_norris_elevation()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        # Keep the last good file rather than publishing nothing.
        try:
            prev = json.load(open(OUT_FILE))
            prev["stale"] = True
            json.dump(prev, open(OUT_FILE, "w"), indent=2)
        except FileNotFoundError:
            pass
        sys.exit(1)

    data = {
        "lake": "Norris",
        "elevation": round(ft, 1),
        "date": date,
        "full_pool": FULL_POOL,
        "below_full_pool": round(FULL_POOL - ft, 1),
        "updated": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    json.dump(data, open(OUT_FILE, "w"), indent=2)
    print(json.dumps(data))


if __name__ == "__main__":
    main()
