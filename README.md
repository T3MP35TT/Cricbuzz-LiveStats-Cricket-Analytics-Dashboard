# 🏏 Cricbuzz LiveStats — Cricket Analytics & Decision Support Platform

Cricbuzz LiveStats is an end-to-end cricket analytics platform that combines **Python, SQL, SQLite, pandas, Streamlit, REST APIs, statistical analysis, and interactive visualization** to transform historical and live cricket data into actionable player, team, match, venue, and performance insights.

🔗 **Live Streamlit Dashboard:** https://cricbuzz-livestats-cricket-analytics-dashboard-kartikey-singh.streamlit.app/


![Cricbuzz LiveStats Dashboard](data/Images/Cricbuzz-LiveStats-Cricket-Analytics-Dashboard)


## 📌 Project Overview

Cricket generates large volumes of structured data across players, teams, matches, innings, venues, partnerships, rankings, and formats.

Cricbuzz LiveStats transforms this data into an interactive analytical product designed to answer questions such as:

- 🏏 Which players are performing best across formats?
- 🏆 Which teams have the strongest winning records?
- 🏠 How does performance differ between home and away matches?
- 🪙 Is winning the toss associated with a higher probability of winning?
- 🎯 Which bowlers demonstrate strong efficiency?
- 📊 Which players show greater batting consistency?
- 🔥 Who is currently showing strong recent form?
- 🤝 Which batting partnerships are the most productive?
- 📈 Which players are improving or declining over time?
- ⚔️ How do teams perform against specific opponents?
- 🏟️ How does venue context relate to player and match performance?

The project demonstrates how a Data Analyst can move from raw data to structured analysis, statistical evaluation, visualization, and decision support.


## 🎯 Business & Analytical Objectives

The project was designed to demonstrate practical analytical workflows across several areas:

- Analyze player performance across **Test, ODI, and T20I**
- Compare team performance and winning records
- Evaluate home vs away performance
- Analyze match and venue characteristics
- Examine toss decisions and match outcomes
- Measure batting and bowling efficiency
- Identify consistent performers
- Evaluate recent player momentum
- Analyze high-value batting partnerships
- Compare team head-to-head performance
- Track performance evolution over time
- Convert analytical results into interactive decision-support views
- Demonstrate SQL proficiency through 25 progressively complex analytical challenges


## 📊 Dataset & Key Metrics

The analytical database currently contains approximately:

| Metric | Records |
|---|---:|
| 🏏 Matches | 22,000+ |
| 👥 Players | 700+ |
| 🏟️ Venues | 600+ |
| 🏏 Batting Records | 81,000+ |
| 🎯 Bowling Records | 57,000+ |
| 🤝 Partnership Records | 35,000+ |

The relational structure allows player, match, venue, series, batting, bowling, partnership, ranking, and classification data to be analyzed together.


## 🧠 Analytical Framework

Cricbuzz LiveStats uses multiple analytical perspectives rather than relying on a single leaderboard.

### 👤 Player Analytics

Player performance can be evaluated across:

- Test
- ODI
- T20I

Key metrics include:

- Runs
- Batting average
- Strike rate
- Wickets
- Economy rate
- Catches
- Stumpings
- Match experience
- Recent form
- Performance consistency

### 🏆 Team Analytics

Team-level analysis includes:

- Team rankings
- Winning records
- Home vs away performance
- Head-to-head records
- Match outcomes
- Competitive strength

### 🏟️ Match & Venue Analytics

Match intelligence includes:

- Toss decisions
- Match outcomes
- Close matches
- Venue characteristics
- Bowling efficiency
- Historical venue signals

### 🤝 Partnership Analytics

Partnership analysis evaluates player combinations using:

- Partnership frequency
- Average partnership runs
- 50+ partnerships
- Highest partnership
- Partnership success rate

### 📈 Time-Based Analytics

The platform introduces temporal analysis through:

- Recent-form analysis
- Recent batting momentum
- Yearly performance comparisons
- Quarterly performance evolution


## 🔎 SQL Analytics — 25 Analytical Challenges

The project contains **25 SQL-driven analytical challenges** designed to progress from fundamental querying to multi-dimensional performance analysis.

### 🟢 Beginner — Q1–Q8

| Query | Analytical Focus |
|---|---|
| Q1 | Indian player profiles |
| Q2 | Recent matches |
| Q3 | Top ODI run scorers |
| Q4 | High-capacity venues |
| Q5 | Team winning records |
| Q6 | Player role distribution |
| Q7 | Highest individual score by format |
| Q8 | Series analysis |

### 🟡 Intermediate — Q9–Q16

| Query | Analytical Focus |
|---|---|
| Q9 | All-rounder performance |
| Q10 | Recent completed matches |
| Q11 | Cross-format player comparison |
| Q12 | Home vs Away performance |
| Q13 | High-value partnerships |
| Q14 | Bowling performance by venue |
| Q15 | Close-match performance |
| Q16 | Yearly batting trends |

### 🔴 Advanced — Q17–Q25

| Query | Analytical Focus |
|---|---|
| Q17 | Toss-performance association |
| Q18 | Limited-overs bowling efficiency |
| Q19 | Batting consistency |
| Q20 | Multi-format experience |
| Q21 | Weighted player performance |
| Q22 | Team head-to-head analysis |
| Q23 | Recent form and momentum |
| Q24 | Partnership performance |
| Q25 | Recent performance evolution |

The broader analytical workflow is:

```text
Business Question
        ↓
SQL Query
        ↓
Result
        ↓
Validation
        ↓
Visualization
        ↓
Interpretation
```

##🧮 Advanced Performance Analytics

The project goes beyond traditional statistics by combining multiple analytical dimensions.

###🪙 Toss Analysis

Q17 evaluates the relationship between toss decisions and match outcomes.

The analysis compares outcomes based on whether the team winning the toss chose to:

Bat first
Bowl first

The results are treated as an observed association rather than proof of causation.

###🎯 Bowling Efficiency

Bowling analysis considers multiple dimensions including:

Economy rate
Wickets
Match participation
Venue performance

This provides a more meaningful comparison than ranking bowlers using wickets alone.

###📊 Batting Consistency

Consistency analysis combines:

Average runs
Standard deviation
Minimum balls faced per innings

The objective is to distinguish consistent run production from averages influenced by a small number of high-scoring performances.

### 🧠 Weighted Performance Ranking

Q21 combines batting, bowling, and fielding-related metrics into a single **project-generated analytical score**.

#### 🏏 Batting Score

```text
(runs × 0.01)
+ (batting average × 0.5)
+ (strike rate × 0.3)
```

#### 🎯 Bowling Score

```text
(wickets × 2)
+ ((50 - bowling average) × 0.5)
+ ((6 - economy rate) × 2)
```

#### 🧤 Fielding Score

```text
(catches × 3)
+ (stumpings × 5)
```

Players are then ranked within each format based on the calculated analytical score.

> ⚠️ **Note:** The weighted score is a project-generated analytical model and is **not an official cricket rating**.

## 🔥 Recent Form & Momentum

Q23 introduces a distinction between **historical performance and current momentum**.

The analysis considers:

- 📊 Average runs in the last 5 performances
- 📊 Average runs in the last 10 performances
- 📈 Strike-rate trend
- 🏏 50+ scores
- 📉 Standard deviation
- 🎯 Consistency score

Players are categorized as:

```text
🔥 Excellent Form
🟢 Good Form
🟡 Average Form
🔴 Poor Form
```

This allows the dashboard to answer:

> **Who is performing well right now?**

rather than relying exclusively on long-term career statistics.

## 📅 Recent Performance Evolution

Q25 introduces a time-based perspective by comparing player performance across six qualifying quarters from **2025 Q1 through 2026 Q2**.

The analysis evaluates:

- 📊 Average runs
- 📈 Strike rate
- 🔄 Quarter-over-quarter movement
- 📉 Performance trajectory

Players are categorized as:

```text
📈 Ascending
➡️ Stable
📉 Declining
```

This shifts the analytical question from:

> Who is performing well?

to:

> **Who is improving, maintaining performance, or declining?**

## ⚡ Live Match Intelligence

Cricbuzz LiveStats combines historical analytics with current cricket information through REST API integration.

The live-match experience provides:

- 🏏 Live match information
- 📊 Match status
- 🏃 Current scores
- 👥 Team information
- 👤 Player information
- 💬 Commentary
- 📋 Scorecards
- 📈 Historical trends
- 🎯 Player performance
- ⚔️ Head-to-head signals
- 🏟️ Venue signals
- 🔥 Recent form
- 🧠 Prediction context

The objective is to go beyond simply displaying a live score.

> 🏏 **A score tells you what is happening. Analytics helps explain the context around it.**

## 🌐 Live API & Fallback Architecture

Live data introduces an important reliability challenge: external APIs can become unavailable, slow, rate-limited, inconsistent, or incomplete.

Cricbuzz LiveStats therefore incorporates API caching and fallback handling where appropriate.

```text
🌐 API
 ↓
🔍 Data availability check
 ↓
⚠️ Response validation
 ↓
🚨 Failure detection
 ↓
🛡️ Fallback / cached / historical source
 ↓
✅ Data validation
 ↓
📊 Analytical layer
 ↓
👤 User-facing output
```

The design principle is:

> **Live data when available. Reliable application behaviour when it isn't.**

This separates the live-data experience from the historical analytical database so that temporary API issues do not invalidate the broader analytical platform.

## 🛡️ Data Quality & Defensive Analytics

Analytical accuracy depends on more than writing correct SQL.

The project considers:

- 🔍 Missing values
- ⚠️ Invalid records
- 🔄 Duplicate or inconsistent information
- 🌐 Data availability
- 🎯 Qualification thresholds
- 🏁 Match completion status
- 📊 Minimum sample sizes

Several analytical queries require sufficient observations before players or teams qualify.

This reduces the risk of drawing conclusions from extremely small samples.

## 🎨 Context-Aware Dashboard Experience

The dashboard includes a dynamic sidebar that changes based on the section being viewed.

### ⚡ Live Matches

Provides context around:

- 🏏 Current match information
- 🔄 Data refresh status
- 📊 Relevant live information

### 🏆 Rankings & Fantasy

Provides:

- 🏆 Top teams
- 👤 Top players
- 🔎 Scouting indicators
- 📊 Player-specific metrics

### 📊 SQL Analytics

Provides query-specific information such as:

- 🔢 Rows analyzed
- 👥 Role distributions
- 📋 Available profiles

### 🛠️ CRUD

Provides database-oriented information such as:

- 👥 Total players
- ✅ Active players
- 🌍 Countries
- 🎯 Roles

This makes the sidebar more than navigation.

It becomes a **context-aware analytical layer**.

## 🧠 Fantasy Analytics

The Fantasy Cricket Arena converts analytical outputs into user-friendly decision-support indicators.

Player analysis can include:

- ⭐ Impact score
- 📊 Recent average
- 📈 Strike rate
- 🔥 50+ scores
- 💥 Boundary potential
- 🚀 Recent momentum

Players can be classified using project-generated signals such as:

> ⭐ **Elite Pick**

These are analytical indicators created within the project and are **not official fantasy ratings**.

## 🎮 Gamified Analytics Experience

The SQL Analytics section is designed as an interactive analytical experience rather than a static SQL-output page.

Users can:

- 🔎 Explore analytical challenges
- 💻 View the underlying SQL
- ▶️ Execute queries
- 📊 Explore returned datasets
- 📈 Interact with charts
- ⚔️ Compare players and teams
- 🔥 Identify performance trends
- 📥 Download analytical results

This combines **SQL analysis, exploratory analytics, visualization, and dashboard storytelling**.

## 🛠️ CRUD & Database Operations

The application also includes an operational database layer.

Users can:

- ➕ Create player records
- 👁️ Read player information
- ✏️ Update player records
- 🗑️ Delete player records

Player information includes:

- 👤 Name
- 🌍 Country
- 🎯 Role
- 🏏 Batting style
- 🎳 Bowling style

This extends the project beyond:

```text
Read → Analyze → Visualize
```

into:

```text
Create → Read → Update → Delete
```

The database therefore supports both **analytical and operational workflows**.

## 🗄️ Data Architecture

Cricbuzz LiveStats uses a relational SQLite database containing match, player, venue, series, batting, bowling, partnership, ranking, and classification data.

### Core Analytical Tables

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

The relational model allows analytical joins across multiple cricket entities rather than treating the dataset as one flat table.

## 🔄 Data Pipeline

```text
                    🌐 Cricket API
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
                    🗄️ SQLite DB
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
          🔎 SQL Layer         🐍 Python/pandas
              │                     │
              └──────────┬──────────┘
                         ▼
                  ⚡ Streamlit
                         │
                         ▼
                  📊 Interactive
                     Insights
```

## 💻 Technical Stack

| Technology | Purpose |
|---|---|
| 🐍 Python | Data processing, analytics and application logic |
| 🔎 SQL | Relational data analysis |
| 🗄️ SQLite | Analytical database |
| 🐼 pandas | Data manipulation and transformation |
| ⚡ Streamlit | Interactive dashboard application |
| 🌐 REST APIs | Live cricket data integration |
| 📊 Interactive Charts | Data visualization and analytical storytelling |
| 🔐 python-dotenv | Environment configuration |
| 🌿 Git | Version control |
| 🐙 GitHub | Repository and project management |

## 📊 Data Analyst Skills Demonstrated

### 🔎 SQL

- SELECT
- Filtering
- JOINs
- GROUP BY
- Aggregations
- CASE expressions
- Date-based analysis
- Conditional aggregation
- CTEs
- Window functions
- Ranking
- Statistical calculations
- Multi-table analysis
- Comparative analysis

### 🐍 Python

- pandas
- Data transformation
- Data validation
- API integration
- Database connectivity
- Statistical calculations
- Application logic
- Error handling

### 📈 Data Visualization

- KPI cards
- Ranking visualizations
- Comparative charts
- Trend analysis
- Performance distributions
- Interactive filtering
- Player comparisons
- Analytical dashboards

### 🧠 Data Analytics

- Descriptive analytics
- Exploratory analysis
- Comparative analytics
- Trend analysis
- Performance measurement
- Consistency analysis
- Time-based analysis
- Segmentation
- Ranking systems
- Decision-support analytics
  
##📁 Project Structure
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

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/T3MP35TT/Cricbuzz-LiveStats-Cricket-Analytics-Dashboard.git
cd Cricbuzz-LiveStats-Cricket-Analytics-Dashboard
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

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

```env
CRICBUZZ_API_KEY=your_api_key
CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com
```

Keep API credentials private and never commit `.env`.

### 5. Run the Dashboard

```bash
streamlit run app.py
```

## 📚 Documentation

Detailed project documentation is available in the `Documentation/` directory.

| Document | Purpose |
|---|---|
| `README.md` | Project overview |
| `PROJECT_SETUP.md` | Installation and setup |
| `API_CONFIGURATION.md` | API configuration, caching and API handling |
| `DATABASE_SCHEMA.md` | Database architecture |
| `SQL_ANALYTICS.md` | Complete Q1–Q25 SQL analytics |
| `PROJECT_DELIVERABLES.md` | Project deliverables and acceptance criteria |

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

## 💡 Key Design Principles

### 1. 📥 Data First

Start with structured, validated data before building analytical outputs.

### 2. 🗄️ Relational Thinking

Use a relational database to connect players, matches, venues, series, partnerships, and performance records.

### 3. 🔎 Analytical SQL

Use SQL not only for extraction, but for aggregation, comparison, ranking, segmentation, and performance analysis.

### 4. 📊 Multiple KPIs

Avoid relying on a single metric when the analytical question requires multiple dimensions.

### 5. 🛡️ Data Reliability

Consider missing data, sample sizes, API failures, caching, and fallback behaviour.

### 6. 🎨 User-Centered Analytics

Present analytical results through interactive interfaces that allow users to explore the data themselves.

### 7. 💡 Decision Support

The objective is not simply to display statistics, but to provide context that helps users interpret performance.

## 📈 Why This Project Matters

Cricbuzz LiveStats demonstrates more than the ability to create a cricket dashboard.

It brings together the complete analytical workflow:

```text
📥 Data Ingestion
↓
🛡️ Data Validation
↓
🗄️ Relational Modelling
↓
🔎 SQL
↓
🐍 Python
↓
🧠 Analytical Models
↓
📊 Visualization
↓
🌐 API Integration
↓
🛡️ Fallback Behaviour
↓
👤 User Interaction
```

The same analytical workflow can be adapted beyond sports analytics to areas such as:

- 💰 Sales analytics
- 👥 Customer analytics
- 💵 Financial analytics
- ⚙️ Operations analytics
- 📦 Product analytics
- 📈 Performance analytics

## 🎓 What This Project Demonstrates

Cricbuzz LiveStats demonstrates practical experience across:

- 📥 Data collection and preparation
- 🛡️ Data cleaning and validation
- 🗄️ Relational database design
- 🔎 SQL analytics
- 🐍 Python data analysis
- 📊 Statistical analysis
- 🎯 KPI development
- 📈 Performance measurement
- 📉 Trend analysis
- 🎯 Consistency analysis
- 📊 Interactive visualization
- 🌐 API integration
- 🛡️ Fallback and reliability design
- ⚡ Dashboard development
- 🛠️ Database CRUD operations
- 📖 Data storytelling
- 💡 Decision-support design

The broader objective is to demonstrate the ability to take a real-world analytical problem and move through:

```text
Data
 ↓
🛡️ Data Quality
 ↓
🗄️ Data Model
 ↓
🔎 Analysis
 ↓
✅ Validation
 ↓
📊 Visualization
 ↓
🎨 User Experience
 ↓
💡 Decision Support
```

## ⭐ Project Highlights

```text
🏏 22,000+ Matches
        +
👥 700+ Players
        +
🏟️ 600+ Venues
        +
🔎 25 SQL Analytics Challenges
        +
🌐 Live Cricket API Integration
        +
🗄️ SQLite Analytical Database
        +
🐍 Python Data Analysis
        +
📊 Interactive Streamlit Dashboard
        +
🧠 Advanced Performance Analytics
        +
🔥 Recent Form & Momentum
        +
📈 Performance Evolution
        +
🎮 Gamified Analytics Experience
        +
🛡️ Fallback & Reliability
        +
🛠️ CRUD Database Operations
```

---
## 👤 Author

**Kartikey Singh**

**Data Analyst | Power BI | Python | SQL | Excel**

🔗 LinkedIn: *[Kartikey_Singh](https://www.linkedin.com/in/btwitskartiksinghdatanalyst/)*

💻 GitHub: *[Kartikey_Singh](https://github.com/T3MP35TT)*

💼 Portfolio : *[Kartikey_Singh](https://sites.google.com/view/kartikeysingh09/home)*

🌐 Live Dashboard: *[Cricbuzz-LiveStats-Cricket-Analytics-Dashboard](https://cricbuzz-livestats-cricket-analytics-dashboard-kartikey-singh.streamlit.app/)*

📝 Complete WriteUp: *[Kartikey_Singh](https://medium.com/@kartikey.singh09/cricbuzz-livestats-building-an-end-to-end-cricket-analytics-product-with-python-sql-and-607b4594d6bc)*


⭐ If you find the project useful, consider giving the repository a star.
