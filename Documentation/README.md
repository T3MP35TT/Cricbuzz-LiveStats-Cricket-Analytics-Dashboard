# Cricbuzz LiveStats Documentation

Cricbuzz LiveStats is an interactive cricket analytics application built with Python and Streamlit. It combines live cricket information, player statistics and rankings, a relational SQLite analytics layer, 25 SQL practice challenges, interactive visualizations, API caching/fallback behavior, and player-record management.

## Documentation

- `PROJECT_SETUP.md` — local installation, database initialization, testing, and running the dashboard.
- `API_CONFIGURATION.md` — API credentials, environment variables, caching, and fallback behavior.
- `DATABASE_SCHEMA.md` — database architecture and table inventory.
- `SQL_ANALYTICS.md` — the complete Q1–Q25 question set and the production SQL used by the analytics module.
- `PROJECT_DELIVERABLES.md` — complete project deliverables and acceptance checklist.

## Main Application Areas

The project is organized around these functional areas:

1. **Home** — project overview and navigation.
2. **Live Matches** — current cricket information from the API layer.
3. **Top Player Stats / Rankings** — format-specific player rankings and statistics.
4. **SQL Queries & Analytics** — 25 executable SQL challenges with result tables, interactive analytics, insights, and CSV export.
5. **CRUD Operations** — player record create/read/update/delete workflows.

## Technology Stack

- Python
- Streamlit
- SQLite
- SQL
- pandas
- Requests
- python-dotenv
- Interactive charting components
- Git / GitHub

## Data Architecture

```text
Live Cricket API
      |
      v
API Helper
      |
      +----> Live response
      |
      +----> Persistent API cache
      |
      v
SQLite historical database
      |
      +----> Player statistics
      +----> Match statistics
      +----> SQL analytics
      +----> CRUD records
      |
      v
Streamlit dashboard
```

## SQL Analytics

The SQL Analytics module contains 25 questions:

- **Beginner:** Q1–Q8
- **Intermediate:** Q9–Q16
- **Advanced:** Q17–Q25

The production query file states that the queries are written for SQLite. Window functions used by advanced queries require a modern SQLite version; the project documentation recommends a current SQLite installation.

## API Resilience

The application uses a layered data strategy:

```text
Live API
   ↓
Persistent API Cache
   ↓
Historical SQLite data where applicable
```

This reduces repeated API requests and provides useful fallback behavior when live data is unavailable.

## Security

Do not commit:

- `.env`
- API keys
- GitHub tokens
- Passwords
- Other private credentials

Use `.env.example` as the public configuration template.

## Repository Structure

```text
cricbuzz_livestats/
├── app.py
├── requirements.txt
├── .env.example
├── documentation/
├── pages/
├── utils/
├── sql_queries/
└── data/
```

## Quick Start

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure `.env`, initialize/populate the database as required, then run:

```bash
streamlit run app.py
```

## Source of Truth

`SQL_ANALYTICS.md` is based on the uploaded production query file containing the project's Q1–Q25 query definitions. The documentation preserves the current query behavior rather than replacing it with generic SQL examples.
