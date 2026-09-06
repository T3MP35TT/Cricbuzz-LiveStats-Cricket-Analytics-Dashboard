# Project Setup

## 1. Prerequisites

Install:

- Python 3.10+
- pip
- Git
- SQLite
- Internet access for live API functionality

Verify Python:

```bash
python --version
```

## 2. Clone the Repository

```bash
git clone https://github.com/T3MP35TT/Cricbuzz-LiveStats-Cricket-Analytics-Dashboard.git
cd Cricbuzz-LiveStats-Cricket-Analytics-Dashboard
```

## 3. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

The project uses Streamlit, pandas, requests, database support, environment-variable management, and the visualization dependencies used by the dashboard.

## 5. Configure Environment Variables

Create `.env` in the project root using `.env.example` as the template.

Typical API configuration:

```env
CRICBUZZ_API_KEY=your_rapidapi_key
CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com
```

Do not commit the real `.env`.

## 6. Database

The main SQLite database is:

```text
data/cricbuzz_livestats.db
```

The schema definition is:

```text
data/schema.sql
```

Supporting scripts include:

```text
data/seed_sample_data.py
data/ingest_players_from_csv.py
data/ingest_cricsheet.py
```

Use the ingestion/seed scripts appropriate to the local dataset state.

## 7. Run the Application

```bash
streamlit run app.py
```

If the Streamlit command is unavailable:

```bash
python -m streamlit run app.py
```

## 8. Functional Test Plan

### Home

- Page loads without exceptions.
- Navigation is visible.
- Project overview is displayed.

### Live Matches

- API data loads when credentials/network are available.
- Cached responses are used when appropriate.
- API failures do not crash the dashboard.

### Player Stats / Rankings

Test:

- ODI
- Test
- T20I

Verify player names, rankings, statistics, and fallback behavior.

### SQL Analytics

Test representative queries from every difficulty level:

```text
Q1, Q8
Q9, Q16
Q17, Q25
```

Then test all Q1–Q25 before release.

Verify:

- Query selection
- SQL display
- Query execution
- Result table
- Query-specific analytics
- CSV export where available

### CRUD

Test:

- Create
- Read
- Update
- Delete

Use a safe test record and verify the final database state.

## 9. Database Inspection

Using SQLite:

```bash
sqlite3 data/cricbuzz_livestats.db
```

List tables:

```sql
.tables
```

Inspect a table:

```sql
.schema players
```

Preview records:

```sql
SELECT * FROM players LIMIT 10;
```

Exit:

```text
.quit
```

## 10. API Cache

Cached API responses are stored under:

```text
data/api_cache/
```

Do not confuse generated cache data with application source code.

## 11. Development Workflow

Before editing:

```bash
git status
```

Review changes:

```bash
git diff
```

Run the application and tests.

Then:

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

## 12. Troubleshooting

### Missing module

```bash
pip install -r requirements.txt
```

### Streamlit not found

```bash
python -m streamlit run app.py
```

### API unavailable

Check:

- API key
- API host
- `.env`
- network
- API usage limits
- `data/api_cache/`

### SQL returns no rows

Check whether the required historical tables have been populated.

### Database mismatch

Compare the live database with `data/schema.sql` and the tables referenced by the relevant query.

## 13. Release Checklist

- [ ] Dependencies install successfully
- [ ] `.env` is excluded from Git
- [ ] Database is available
- [ ] API configuration works
- [ ] Cache behavior works
- [ ] All dashboard pages load
- [ ] Q1–Q25 execute
- [ ] CRUD operations work
- [ ] Documentation is updated
- [ ] Git status contains only intended changes
