# Norris lake level feed

Publishes `norris-level.json` once a day so lakenorrischalets.com can show
the current elevation. Runs on GitHub Actions; nothing to host.

## Setup (about 10 minutes)

1. Go to github.com, sign in (or make a free account), click **New repository**.
   Name it `norris-lake-level`, leave it **Public**, click Create.
2. Click **uploading an existing file** and drag in everything from this folder
   (`update_level.py`, `README.md`, and the `.github` folder). Commit.
3. Open the **Actions** tab. If it asks you to enable workflows, click enable.
4. Click **Update Norris lake level** on the left, then **Run workflow**.
   Wait a minute, refresh, and you should see a green check and a new
   `norris-level.json` in the repo.
5. Click that file, then **Raw**. Copy the URL. It will look like
   `https://raw.githubusercontent.com/YOUR-USERNAME/norris-lake-level/main/norris-level.json`
6. In the website code, find `var LEVEL_URL = "";` and paste that URL between
   the quotes. Republish the Squarespace page.

From then on it updates itself every morning. If TVA changes their page and
the fetch stops working, the Actions tab shows a red X and the site keeps
showing the last good reading with `"stale": true` in the file.

## If you already have a script that gets the elevation

Open `update_level.py`, paste your fetch code inside `get_norris_elevation()`
where the comment says to, and make it `return float(elevation), "YYYY-MM-DD"`.
Everything else stays the same.
