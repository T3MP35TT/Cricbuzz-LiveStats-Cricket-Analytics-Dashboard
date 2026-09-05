# Cricbuzz LiveStats

Real-time cricket dashboard: live scores via the Cricbuzz API, plus 25
SQL analytics queries and CRUD tooling running against a local database
seeded from historical datasets — so the analytics module never touches
your API quota.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # then add your Cricbuzz RapidAPI key
python data/seed_sample_data.py   # creates DB + demo rows, app works immediately
streamlit run app.py
```

## Loading real data (optional, recommended)

1. **Player career stats** — download a Kaggle dataset such as
   "International Cricket Player Performance Stats" (Ijaj Ahmed), then:
   ```bash
   python data/ingest_players_from_csv.py path/to/downloaded.csv
   ```
   Adjust `COLUMN_MAP` in that script if the CSV's column names differ.

2. **Matches, innings, partnerships** — download a *filtered* subset from
   [cricsheet.org](https://cricsheet.org/downloads/) (one format / a few
   years — not the full multi-GB archive), then:
   ```bash
   python data/ingest_cricsheet.py path/to/cricsheet_json_folder/
   ```

3. **Venues** — copy Wikipedia's "List of cricket grounds by capacity"
   table into `venues` (small enough to do by hand or with
   `pandas.read_html`).

4. **Series / "last 30 days" matches** — pulled live from the Cricbuzz
   API and cached (see `utils/api_helper.py`), refreshed at most a few
   times a day — never on every page load.

## Why the API is barely used

Only two pages touch the live API: **Live Matches** and part of
**Top Player Stats**. Every response is cached to disk
(`data/api_cache/`) with a TTL per endpoint type — a couple of minutes
for live scores, up to 30 days for things like career stats or series
info that rarely change. The **SQL Queries & Analytics** page never
calls the API at all; it only reads the local database, so running any
of the 25 queries costs zero API calls no matter how many times you run it.

## Swapping the database

Everything goes through `utils/db_connection.py`. It uses SQLite by
default (zero setup). To use PostgreSQL or MySQL instead, replace
`get_connection()` with a `psycopg2`/`mysql-connector` connection —
no other file needs to change.
