# Database Schema

## 1. Database

Primary SQLite database:

```text
data/cricbuzz_livestats.db
```

Schema definition:

```text
data/schema.sql
```

## 2. Purpose

The database provides the persistent analytical layer for:

- Players
- Career statistics
- Batting
- Bowling
- Matches
- Scorecards
- Innings
- Partnerships
- Venues
- Series
- Team classification
- ICC rankings
- Specialized Q22/Q23 analytics
- CRUD player records

## 3. Current Table Inventory

The inspected project database contains the following 25 tables:

```text
2024_matches
Q23_batting_innings_SR
allrounder_player_map
cricinfo_active_players
cricsheet_batting_match
cricsheet_bowling_match
cricsheet_q22_match_details
icc_rankings_odi
icc_rankings_t20
icc_rankings_test
innings_scores
match_scorecards
matches
partnerships
player_allrounder_stats
player_bowling_stats
player_career_stats
player_roles_admin
player_roles_reference
players
q23_player_aliases
series
team_classification
top_partnerships_reference
venues
```

## 4. Core Relationship Model

Conceptually:

```text
players
  |
  +--> player_career_stats
  +--> player_bowling_stats
  +--> player_allrounder_stats
  +--> player_roles_admin
  +--> player_roles_reference
  +--> Q23_batting_innings_SR
  +--> q23_player_aliases

matches
  |
  +--> innings_scores
  +--> match_scorecards
  +--> cricsheet_batting_match
  +--> cricsheet_bowling_match
  +--> cricsheet_q22_match_details
  +--> venues
  +--> series

partnerships
  |
  +--> players

team_classification
  |
  +--> matches.winner / team names
```

## 5. Important Tables

### players

Central player identity table used to connect player IDs to player names.

### player_roles_admin

Administrative player role/profile information used by Q1 and Q6.

### player_roles_reference

Reference player information used by analytical queries such as Q18.

### player_career_stats

Career-level format statistics used by Q3, Q11, Q18, Q20, and Q21.

### player_bowling_stats

Bowling-level career/format statistics used by Q18.

### player_allrounder_stats

All-rounder statistics used by Q9.

### allrounder_player_map

Maps the all-rounder dataset to player identities and roles for Q9.

### matches

Central match-level table used throughout the SQL analytics layer.

### venues

Venue metadata used by Q2, Q4, Q10, Q12, Q14, and Q22 venue analysis.

### innings_scores

Innings-level batting information used by Q7, Q15, Q16, Q19, Q20-related analytics, and Q25.

### partnerships

Partnership-level records used by Q24 and related partnership analytics.

### top_partnerships_reference

Reference partnership results used by Q13.

### team_classification

Team metadata used by Q5.

### series

Series information used by series-level analytics.

### ICC ranking tables

```text
icc_rankings_odi
icc_rankings_test
icc_rankings_t20
```

These support format-specific ranking experiences.

## 6. Specialized Analytics Tables

Q22:

```text
cricsheet_q22_match_details
```

Q23:

```text
Q23_batting_innings_SR
q23_player_aliases
```

These tables provide specialized data needed by the corresponding advanced analytics.

## 7. 2024 Archive

```text
2024_matches
```

Q8 uses this table to analyze series that started in 2024.

## 8. Database Population

Supporting scripts include:

```text
data/seed_sample_data.py
data/ingest_players_from_csv.py
data/ingest_cricsheet.py
```

Use the appropriate script for the dataset being initialized.

## 9. Schema Integrity

Before changing schema:

1. Back up the database.
2. Update `data/schema.sql`.
3. Update affected queries.
4. Update ingestion scripts if necessary.
5. Test Q1–Q25.
6. Test CRUD.
7. Verify existing application pages.

## 10. SQL-to-Table Mapping

| Query | Main data areas |
|---|---|
| Q1 | player_roles_admin |
| Q2 | matches, venues, cricsheet_bowling_match |
| Q3 | player_career_stats, players |
| Q4 | venues |
| Q5 | matches, team_classification |
| Q6 | player_roles_admin |
| Q7 | innings_scores, matches, players |
| Q8 | 2024_matches |
| Q9 | player_allrounder_stats, allrounder_player_map |
| Q10 | matches, venues |
| Q11 | player_career_stats, players |
| Q12 | matches, venues |
| Q13 | top_partnerships_reference |
| Q14 | cricsheet_bowling_match |
| Q15 | innings_scores, matches, players |
| Q16 | innings_scores, matches, players |
| Q17 | matches |
| Q18 | player_bowling_stats, player_roles_reference |
| Q19 | innings_scores, players |
| Q20 | player_career_stats, players |
| Q21 | player_career_stats, players |
| Q22 | matches, cricsheet_q22_match_details |
| Q23 | Q23_batting_innings_SR, players |
| Q24 | partnerships, players |
| Q25 | innings_scores, players |

## 11. Important Note

This document records the table inventory and table usage supported by the current project query layer. It does not invent column definitions that are not established by the project source. For exact column-level DDL, use `data/schema.sql` as the authoritative schema file.
