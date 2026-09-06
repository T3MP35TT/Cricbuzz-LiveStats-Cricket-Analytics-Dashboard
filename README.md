# 🏏 Cricbuzz LiveStats — Cricket Analytics Dashboard

An end-to-end cricket analytics platform built with **Python, SQL, SQLite, Streamlit, REST APIs, and interactive data visualizations**. The project combines live cricket data with structured historical datasets to demonstrate practical data analysis, database querying, KPI development, and interactive dashboard design.

🔗 **Repository:** https://github.com/T3MP35TT/Cricbuzz-LiveStats-Cricket-Analytics-Dashboard

---

## 📊 Project Overview

**Cricbuzz LiveStats** is an interactive cricket analytics application designed to transform raw cricket data into meaningful insights through a combination of **data engineering, SQL analytics, statistical analysis, and dashboard visualization**.

The project goes beyond basic dashboards by incorporating **25 SQL analytics challenges**, player performance analysis, team and venue analysis, recent-form analysis, head-to-head analytics, batting partnerships, career trends, and live cricket information.

The objective is to demonstrate how a Data Analyst can work across the complete analytics workflow:

```text
Raw Data / APIs
      ↓
Data Collection & Processing
      ↓
Data Cleaning & Transformation
      ↓
SQLite Data Model
      ↓
SQL Analytics
      ↓
Python Analysis
      ↓
Interactive Visualizations
      ↓
Business-Friendly Insights
```

---

## 🎯 Business & Analytical Objectives

The dashboard addresses several analytical questions relevant to sports performance and decision-making:

* Which players are performing best across formats?
* Which teams have the strongest winning records?
* How does performance differ between home and away matches?
* Does winning the toss provide a measurable advantage?
* Which bowlers are the most economical?
* Which batsmen are the most consistent?
* Which players are currently showing strong momentum?
* Which batting partnerships are most successful?
* How do player performances evolve over time?
* How do teams perform against specific opponents?
* Which venues produce different batting or bowling outcomes?

---

## 🛠️ Tech Stack

| Category               | Technologies        |
| ---------------------- | ------------------- |
| Programming            | Python              |
| Database               | SQLite              |
| Query Language         | SQL                 |
| Dashboard              | Streamlit           |
| Data Analysis          | pandas              |
| API Integration        | REST API / Requests |
| Data Processing        | Python              |
| Visualization          | Interactive charts  |
| Environment Management | python-dotenv       |
| Version Control        | Git & GitHub        |

---

## 📌 Key Features

### 🏏 Live Cricket Data

The application integrates cricket API data to provide current match information.

Features include:

* Live match information
* Match status
* Current scores
* Team information
* Player information
* API response caching
* Fallback handling for unavailable API data

---

### 📈 Player Statistics & Rankings

Analyze player performance across:

* Test
* ODI
* T20I

The dashboard supports analysis of:

* Runs
* Batting average
* Strike rate
* Wickets
* Economy rate
* Catches
* Stumpings
* Player rankings

---

### 🔎 SQL Analytics — 25 Analytical Challenges

The project includes **25 SQL-driven analytical questions**, organized into three difficulty levels.

#### Beginner — Q1–Q8

| Query | Analysis                           |
| ----- | ---------------------------------- |
| Q1    | Indian player profiles             |
| Q2    | Matches played in the last 30 days |
| Q3    | Top 10 ODI run scorers             |
| Q4    | High-capacity cricket venues       |
| Q5    | Team winning records               |
| Q6    | Player role distribution           |
| Q7    | Highest individual score by format |
| Q8    | Cricket series started in 2024     |

#### Intermediate — Q9–Q16

| Query | Analysis                         |
| ----- | -------------------------------- |
| Q9    | All-rounder performance          |
| Q10   | Last 20 completed matches        |
| Q11   | Cross-format player comparison   |
| Q12   | Home vs Away performance         |
| Q13   | 100+ batting partnerships        |
| Q14   | Bowling performance by venue     |
| Q15   | Close-match performance          |
| Q16   | Yearly batting trends since 2020 |

#### Advanced — Q17–Q25

| Query | Analysis                              |
| ----- | ------------------------------------- |
| Q17   | Toss advantage                        |
| Q18   | Most economical limited-overs bowlers |
| Q19   | Batting consistency                   |
| Q20   | Multi-format experience               |
| Q21   | Weighted player performance ranking   |
| Q22   | Team head-to-head analysis            |
| Q23   | Recent form & momentum                |
| Q24   | Best batting partnerships             |
| Q25   | Career performance evolution          |

---

## 🧠 Advanced Analytics

### Toss Advantage

Measures the percentage of matches won by the team winning the toss and breaks the analysis down by whether the team chose to:

* Bat first
* Bowl first

### Player Consistency

Uses:

* Average runs
* Standard deviation
* Minimum balls faced per innings

to identify players with more consistent batting performances.

### Recent Form & Momentum

The Q23 analysis evaluates a player's latest batting performances using:

* Average runs in last 5 performances
* Average runs in last 10 performances
* Strike-rate trend
* 50+ scores
* Standard deviation
* Consistency score

Players are classified into:

```text
Excellent Form
Good Form
Average Form
Poor Form
```

### Weighted Performance Ranking

Q21 combines batting, bowling, and fielding into a single performance score.

**Batting:**

```text
(runs × 0.01)
+ (batting average × 0.5)
+ (strike rate × 0.3)
```

**Bowling:**

```text
(wickets × 2)
+ ((50 - bowling average) × 0.5)
+ ((6 - economy rate) × 2)
```

**Fielding:**

```text
(catches × 3)
+ (stumpings × 5)
```

Players are then ranked within each format.

### Career Evolution

Q25 uses quarterly batting performance to analyze:

* Average runs
* Strike rate
* Quarter-over-quarter movement
* Performance trajectory

Players are categorized as:

```text
Career Ascending
Career Stable
Career Declining
```

---

## 🗄️ Data Architecture

The project uses a relational SQLite database containing match, player, venue, series, batting, bowling, partnership, ranking, and classification data.

Major analytical tables include:

```text
players
matches
venues
innings_scores
partnerships
player_career_stats
player_bowling_stats
player_allrounder_stats
player_roles_admin
team_classification
series
```

Specialized analytical datasets support advanced questions such as Q22 and Q23.

---

## 🔄 Data Pipeline

```text
                Cricket API
                    │
                    ▼
             API Helper Layer
                    │
                    ▼
              API Cache
                    │
                    ▼
          Historical / Structured Data
                    │
                    ▼
               SQLite DB
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       SQL Layer          Python/pandas
          │                   │
          └─────────┬─────────┘
                    ▼
             Streamlit Dashboard
                    │
                    ▼
            Interactive Insights
```

---

## 📊 Analytical Skills Demonstrated

This project demonstrates practical experience with:

### SQL

* SELECT statements
* Filtering
* JOINs
* GROUP BY
* Aggregations
* CASE expressions
* Date-based analysis
* Conditional aggregation
* CTEs
* Window functions
* Ranking
* Statistical calculations
* Multi-table analysis
* Comparative analysis

### Python

* pandas
* Data transformation
* Data validation
* API integration
* Database connectivity
* Statistical calculations
* Application logic
* Error handling

### Data Visualization

* KPI cards
* Ranking visualizations
* Comparative charts
* Trend analysis
* Performance distributions
* Interactive filtering
* Player comparisons

### Data Analytics

* Descriptive analytics
* Trend analysis
* Comparative analytics
* Performance measurement
* Consistency analysis
* Time-series analysis
* Segmentation
* Ranking systems

---

## 🎮 Gamified Analytics Experience

The SQL analytics section is designed as an interactive experience rather than a static SQL output page.

Users can:

* Explore individual analytical challenges
* View the underlying SQL
* Execute queries against the database
* Explore returned datasets
* Interact with charts
* Compare players and teams
* Identify performance trends
* Download analytical results

This approach combines **SQL learning, exploratory analysis, and dashboard storytelling** in a single application.

---

## 🖥️ Application Structure

```text
Cricbuzz-LiveStats-Cricket-Analytics-Dashboard/
│
├── app.py
│
├── pages/
│   ├── Live Matches
│   ├── Cricket Rankings & Fantasy
│   ├── SQL Queries & Analytics
│   └── CRUD Operations
│
├── utils/
│   ├── API helpers
│   ├── Database utilities
│   └── Supporting functions
│
├── data/
│   ├── cricbuzz_livestats.db
│   ├── schema.sql
│   ├── api_cache/
│   └── ingestion scripts
│
├── api_test_output/
│
├── Documentation/
│   ├── README.md
│   ├── PROJECT_SETUP.md
│   ├── API_CONFIGURATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── SQL_ANALYTICS.md
│   └── PROJECT_DELIVERABLES.md
│
├── requirements.txt
└── .env.example
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/T3MP35TT/Cricbuzz-LiveStats-Cricket-Analytics-Dashboard.git
cd Cricbuzz-LiveStats-Cricket-Analytics-Dashboard
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```env
CRICBUZZ_API_KEY=your_api_key
CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com
```

Keep API credentials private and never commit `.env`.

### 5. Run the Dashboard

```bash
streamlit run app.py
```

---

## 📚 Documentation

Detailed technical documentation is available in the `Documentation/` directory.

| Document                  | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| `README.md`               | Project overview                             |
| `PROJECT_SETUP.md`        | Installation and setup                       |
| `API_CONFIGURATION.md`    | API configuration and caching                |
| `DATABASE_SCHEMA.md`      | Database architecture                        |
| `SQL_ANALYTICS.md`        | Complete Q1–Q25 SQL analytics                |
| `PROJECT_DELIVERABLES.md` | Project deliverables and acceptance criteria |

---

## 🔐 Security

Sensitive credentials are intentionally excluded from the repository.

Never commit:

```text
.env
API keys
GitHub tokens
Passwords
Private credentials
```

Use `.env.example` as the configuration template.

---

## 📈 Why This Project Matters

This project demonstrates more than the ability to create a dashboard.

It brings together the complete analytical workflow:

**Data Collection → Data Preparation → Data Modeling → SQL → Analysis → Visualization → Insights**

From querying relational data to building statistical performance measures and interactive visualizations, the project demonstrates how technical analytics skills can be applied to a real-world domain.

The same workflow can be adapted to business domains such as:

* Sales analytics
* Customer analytics
* Financial analytics
* Operations analytics
* Product analytics
* Performance analytics

---

## 👤 Author

**Kartikey Singh**

Data Analyst | SQL | Python | Power BI | Data Visualization | Analytics

---

## ⭐ Project Highlights

```text
25 SQL Analytics Challenges
        +
Live Cricket API Integration
        +
SQLite Analytical Database
        +
Python Data Analysis
        +
Interactive Streamlit Dashboard
        +
Advanced Performance Analytics
        +
Gamified User Experience
```

If you find the project useful, consider giving the repository a ⭐ on GitHub.
