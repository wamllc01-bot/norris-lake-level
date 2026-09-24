name: Update Norris lake level

on:
  schedule:
    - cron: "15 12 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Fetch elevation and write JSON
        run: python update_level.py
      - name: Commit if changed
        run: |
          git config user.name "lake-level-bot"
          git config user.email "bot@lakenorrischalets.com"
          git add norris-level.json
          git diff --cached --quiet || git commit -m "Norris level $(date -u +%F)"
          git push
