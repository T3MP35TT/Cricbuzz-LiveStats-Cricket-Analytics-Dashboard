# Cricbuzz LiveStats

## Cricket Analytics Dashboard

Cricbuzz LiveStats is an interactive cricket analytics dashboard built with **Python, Streamlit, SQL, SQLite, Plotly, and the Cricbuzz API**.

The project combines live cricket data, recent match information, ICC player rankings, historical cricket datasets, SQL analytics, interactive visualizations, and database management features in a single Streamlit application.

It is designed as a portfolio project demonstrating practical skills in **data analytics, SQL, Python, data visualization, API integration, database management, caching, and dashboard development**.

---

## Live Application

> Add your deployed Streamlit application URL here after deployment.

**Live Dashboard:** `YOUR_STREAMLIT_APP_URL`

---

## GitHub Repository

**Repository:** `https://github.com/YOUR_USERNAME/cricbuzz-livestats`

---

## Project Overview

Cricbuzz LiveStats provides multiple analytical views for exploring cricket data.

The dashboard includes:

- Live and recent cricket matches
- Detailed match information and scorecards
- ICC batting and bowling rankings
- ODI, Test, and T20 player statistics
- 25 SQL-based cricket analytics queries
- Interactive Plotly charts
- Player database management through CRUD operations
- Historical cricket data stored in SQLite
- Cricbuzz API integration
- Local API response caching
- GitHub-backed cache persistence for deployed environments
- A dark, Cricbuzz-inspired dashboard interface

The project follows a simple architecture where the application retrieves current data from the API first and uses cached data as a fallback when the API is temporarily unavailable.

---

## Features

### 🏏 Live Matches

View currently available cricket matches using Cricbuzz API data.

The Live Matches section provides:

- Live match listings
- Match status
- Teams
- Scores
- Match information
- Recent match results
- Detailed scorecards where available

The application is designed to keep API and cache handling separate from the page-level UI.

---

### 🕒 Recent Matches

Explore recently completed cricket matches.

Recent match information can be retrieved from the API and stored in the project's cache directory. Cached match responses can be reused when the API is temporarily unavailable.

---

### 📊 Top Player Stats

The Top Player Stats section uses imported ICC rankings rather than relying exclusively on live API ranking responses.

Supported formats:

- ODI
- Test
- T20

The dashboard provides separate batting and bowling leaderboards with information such as:

- Rank
- Player
- Country / Team
- Rating
- Career-best rating
- Rating power
- Ranking status

The current ICC ranking data is stored in the SQLite database.

---

### 🔎 SQL Analytics

The SQL Analytics section contains **25 cricket-focused SQL queries** covering different levels of analytical complexity.

The queries demonstrate concepts such as:

- Filtering
- Aggregation
- Grouping
- Sorting
- Joins
- Subqueries
- Window functions
- Ranking
- Match-level analysis
- Player-level analysis
- Team-level analysis
- Performance analysis

The results are presented through Streamlit tables and interactive Plotly visualizations where appropriate.

---

### 📈 Interactive Visualizations

The dashboard uses **Plotly** to provide interactive analytical charts.

Depending on the selected SQL analysis, visualizations can include:

- Bar charts
- Rankings
- Comparative performance charts
- Distribution views
- Trend analysis
- Category comparisons

Charts are integrated directly into the Streamlit interface so users can explore analytical results interactively.

---

### 🛠️ CRUD Operations

The CRUD Operations section provides database management functionality for player records.

Supported operations include:

- Create
- Read
- Update
- Delete

This section demonstrates practical interaction between a Streamlit interface and a relational SQLite database.

---

### 💾 API Caching

The project includes a caching layer in:

```text
utils/api_helper.py
```

The caching system is designed to reduce unnecessary API requests and provide fallback data when the external API cannot be reached.

The general flow is:

```text
Cricbuzz API
      │
      ▼
API Response
      │
      ├──► Local Cache
      │
      └──► GitHub Cache
```

When the API is unavailable:

```text
API unavailable
      │
      ▼
Local cache
      │
      ▼
GitHub cache
      │
      ▼
Available cached data
```

The application does not depend on the API being available at every moment.

---

## API and Cache Strategy

The project follows an **API-first, cache-fallback** approach.

### Normal request

```text
Dashboard
    ↓
Cricbuzz API
    ↓
Fresh response
    ↓
Local cache
    ↓
GitHub cache
    ↓
Dashboard
```

### API failure

```text
Dashboard
    ↓
Cricbuzz API
    ↓
API failure
    ↓
Local cache
    ↓
GitHub cache
    ↓
Dashboard
```

The cache is intended to improve resilience and reduce unnecessary dependency on external API availability.

---

## GitHub-Persistent Cache

Streamlit Cloud uses an ephemeral runtime environment, meaning files written to the application filesystem should not be treated as permanent storage.

To address this for API cache data, the project can persist cache files directly into the GitHub repository.

The GitHub cache integration is implemented inside:

```text
utils/api_helper.py
```

No separate cache service is required.

### GitHub cache configuration

The application can use:

```text
GITHUB_TOKEN
GITHUB_REPO
GITHUB_BRANCH
GITHUB_CACHE_PATH
```

Example:

```env
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/cricbuzz-livestats
GITHUB_BRANCH=main
GITHUB_CACHE_PATH=data/api_cache
```

GitHub persistence is best-effort. If GitHub is unavailable, the dashboard continues using its other available data sources.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application and data processing |
| Streamlit | Web dashboard |
| SQL | Analytical queries |
| SQLite | Relational database |
| Pandas | Data manipulation |
| Plotly | Interactive visualizations |
| Requests | API communication |
| python-dotenv | Local environment configuration |
| OpenPyXL | Excel / ICC ranking data import |
| Cricbuzz API | Live and recent cricket data |
| GitHub Contents API | Persistent API cache |

---

## Project Architecture

```text
                         ┌─────────────────────┐
                         │    Cricbuzz API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  api_helper.py      │
                         │ API + Cache Layer   │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
             ┌───────────────┐             ┌───────────────┐
             │ Local Cache   │             │ GitHub Cache  │
             │ data/api_cache│             │ Repository    │
             └───────────────┘             └───────────────┘

                         ┌─────────────────────┐
                         │      SQLite DB      │
                         │ cricbuzz_livestats  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Streamlit App     │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
       Live Matches          Top Player Stats       SQL Analytics
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    ▼
                            Interactive Dashboard
```

---

## Project Structure

```text
cricbuzz-livestats/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── pages/
│   ├── 1_Home.py
│   ├── 2_Live_Matches.py
│   ├── 3_Top_Player_Stats.py
│   ├── 4_SQL_Queries_Analytics.py
│   └── 5_CRUD_Operations.py
│
├── utils/
│   ├── api_helper.py
│   ├── db_connection.py
│   └── theme.py
│
├── sql_queries/
│   └── queries.py
│
└── data/
    ├── api_cache/
    ├── Images/
    │   ├── IND Players/
    │   ├── background.jpg
    │   ├── header.jpg
    │   └── Indian Flag.png
    ├── cricbuzz_livestats.db
    ├── ingest_cricsheet.py
    ├── ingest_players_from_csv.py
    └── schema.sql
```

---

## Database

The project uses **SQLite** as its primary relational database.

Main database:

```text
data/cricbuzz_livestats.db
```

Database schema:

```text
data/schema.sql
```

The database contains cricket-related historical data, player information, match information, team classifications, and imported ICC rankings used by the dashboard.

---

## ICC Rankings Data

ICC rankings are imported into separate SQLite tables for different formats.

Current ranking tables include:

```text
icc_rankings_odi
icc_rankings_test
icc_rankings_t20
```

The imported ranking data contains batting and bowling records.

The Top Player Stats page queries these tables directly to generate the top 20 batting and bowling leaderboards for each format.

---

## Historical Data

Historical cricket data is processed through the project's ingestion scripts.

Relevant scripts include:

```text
data/ingest_cricsheet.py
data/ingest_players_from_csv.py
```

The database schema is defined in:

```text
data/schema.sql
```

These components provide the foundation for the SQL analytics section of the dashboard.

---

## SQL Analytics

The SQL Analytics page is built around 25 predefined analytical questions.

The query definitions are maintained in:

```text
sql_queries/queries.py
```

The Streamlit page responsible for displaying the analysis is:

```text
pages/4_SQL_Queries_Analytics.py
```

The SQL layer is intentionally separated from the dashboard presentation layer so that analytical logic remains easier to maintain and review.

---

## Configuration

The project supports environment variables for API and GitHub configuration.

Create a local `.env` file:

```env
CRICBUZZ_API_KEY=your_rapidapi_key
CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com

GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/cricbuzz-livestats
GITHUB_BRANCH=main
GITHUB_CACHE_PATH=data/api_cache
```

A template is provided as:

```text
.env.example
```

### Important

Never commit your real `.env` file or API credentials to GitHub.

The `.gitignore` file is configured to exclude local secrets.

---

## Streamlit Cloud Secrets

For Streamlit Cloud deployment, use the application's Secrets configuration instead of committing credentials to the repository.

Example:

```toml
CRICBUZZ_API_KEY = "YOUR_REAL_RAPIDAPI_KEY"
CRICBUZZ_API_HOST = "cricbuzz-cricket.p.rapidapi.com"

GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
GITHUB_REPO = "YOUR_USERNAME/cricbuzz-livestats"
GITHUB_BRANCH = "main"
GITHUB_CACHE_PATH = "data/api_cache"
```

Replace the placeholder values with your actual credentials and repository information.

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cricbuzz-livestats.git
cd cricbuzz-livestats
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create:

```text
.env
```

and add your API and GitHub configuration.

### 5. Run the dashboard

```bash
streamlit run app.py
```

The application will open in your browser.

---

## Requirements

The project uses the following primary dependencies:

```text
streamlit>=1.32
requests>=2.31
pandas>=2.0
python-dotenv>=1.0
openpyxl
plotly>=5.18
psycopg2-binary==2.9.12
```

---

## Deployment

The application is designed to be deployed using **Streamlit Community Cloud**.

### Deployment steps

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Select the GitHub repository.
4. Set the main application file to:

```text
app.py
```

5. Configure the required Streamlit Secrets.
6. Deploy the application.
7. Test API access and cache fallback behavior.

---

## Deployment Checklist

Before deploying, verify:

- [ ] `.env` is not committed
- [ ] API keys are not hardcoded
- [ ] `.venv/` is not committed
- [ ] `__pycache__/` is not committed
- [ ] `requirements.txt` contains Plotly
- [ ] `app.py` runs locally
- [ ] All Streamlit pages load
- [ ] SQLite database is present
- [ ] `data/api_cache/` is available
- [ ] GitHub token has appropriate repository permissions
- [ ] GitHub repository name is configured correctly
- [ ] Streamlit Secrets are configured
- [ ] Live API requests work
- [ ] API fallback to cache works
- [ ] GitHub cache persistence works

---

## Data Flow

### Live and recent match data

```text
Cricbuzz API
     ↓
api_helper.py
     ↓
Cache response
     ↓
Streamlit page
```

### Historical analytics

```text
Historical cricket data
     ↓
SQLite database
     ↓
SQL queries
     ↓
Pandas DataFrame
     ↓
Plotly / Streamlit
```

### ICC rankings

```text
ICC ranking files
     ↓
Ranking import script
     ↓
SQLite ranking tables
     ↓
Top Player Stats page
```

---

## API Error Handling

The dashboard is designed to avoid exposing technical API configuration errors to normal users.

When live API data cannot be retrieved, the application attempts to use available cached data.

The intended user experience is:

```text
Fresh API data
     ↓
if unavailable
     ↓
Cached data
     ↓
if unavailable
     ↓
No data currently available
```

This prevents raw API errors, credentials, hostnames, or implementation details from being displayed unnecessarily in the dashboard.

---

## Database Persistence Note

The SQLite database is suitable for the project's local analytical and demonstration environment.

When deployed to Streamlit Cloud, runtime modifications made through the CRUD interface should **not be considered permanent storage**, because the application's runtime filesystem can be reset.

The GitHub-backed cache is intended specifically for API cache persistence.

For permanent production database writes, a hosted database such as PostgreSQL would be a more appropriate architecture.

---

## Security

The project follows these basic security practices:

- API credentials are stored outside the source code.
- `.env` is excluded from Git.
- Streamlit Secrets can be used for deployment credentials.
- GitHub access tokens should be restricted to the required repository.
- API failures do not expose credentials in the user interface.
- Cache persistence is handled separately from application credentials.

Never place credentials directly inside Python source files.

---

## What This Project Demonstrates

This project demonstrates practical experience with:

### Data Analytics

- Exploratory analysis
- KPI analysis
- Ranking analysis
- Player performance analysis
- Match-level analysis
- Team-level analysis
- Historical data analysis

### SQL

- SELECT statements
- Filtering
- Aggregation
- GROUP BY
- HAVING
- JOIN operations
- Subqueries
- Window functions
- Ranking
- Analytical queries

### Python

- Data processing
- API integration
- Database interaction
- File handling
- Caching
- Application architecture

### Data Visualization

- Interactive Plotly charts
- Analytical dashboards
- Ranking visualizations
- Comparative analysis
- Streamlit data presentation

### Application Development

- Streamlit multipage applications
- SQLite integration
- CRUD functionality
- API error handling
- Cache fallback
- Environment configuration
- Deployment preparation

---

## Future Improvements

Potential future improvements include:

- PostgreSQL integration for persistent database writes
- Additional cricket performance metrics
- More historical datasets
- Advanced player comparison tools
- Team performance dashboards
- Tournament-level analytics
- More granular match filters
- Automated data refresh workflows
- Improved cache write batching
- Additional interactive visualizations

---

## Project Status

**Status:** Deployment-ready portfolio project

The application currently focuses on:

- Cricket analytics
- Live and recent match data
- ICC player rankings
- SQL-based analysis
- Interactive visualizations
- SQLite database operations
- API caching
- Streamlit deployment

---

## Author

**Your Name**

Data Analyst | SQL | Python | Power BI | Tableau | Data Visualization

GitHub: `https://github.com/YOUR_USERNAME`

LinkedIn: `YOUR_LINKEDIN_PROFILE_URL`

---

## License

This project is intended for educational, portfolio, and demonstration purposes.

Add an appropriate open-source license to the repository if you intend to distribute the project under specific licensing terms.

---

## Acknowledgements

Cricket data and APIs used by the project are subject to the terms and availability of their respective providers.

This project is an independent analytics application and is not affiliated with or endorsed by Cricbuzz or the ICC.
