-- Cricbuzz LiveStats schema
-- SQLite database for cricket analytics and player statistics.

-- Player information
CREATE TABLE IF NOT EXISTS players (
    player_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name    TEXT NOT NULL,
    country       TEXT,
    playing_role  TEXT,   -- Batsman / Bowler / All-rounder / Wicket-keeper
    batting_style TEXT,
    bowling_style TEXT,
    UNIQUE(player_name, country)
);

-- Venue information
CREATE TABLE IF NOT EXISTS venues (
    venue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name   TEXT NOT NULL,
    city         TEXT,
    country      TEXT,
    capacity     INTEGER,
    UNIQUE(venue_name, city)
);

-- Series information
CREATE TABLE IF NOT EXISTS series (
    series_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name    TEXT NOT NULL,
    host_country   TEXT,
    match_type     TEXT,     -- Test / ODI / T20I
    start_date     TEXT,     -- ISO date
    total_matches  INTEGER
);

-- Match information
CREATE TABLE IF NOT EXISTS matches (
    match_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id       INTEGER REFERENCES series(series_id),
    description     TEXT,
    team1           TEXT,
    team2           TEXT,
    venue_id        INTEGER REFERENCES venues(venue_id),
    match_date      TEXT,     -- ISO date
    match_type      TEXT,     -- Test / ODI / T20I
    toss_winner     TEXT,
    toss_decision   TEXT,     -- bat / bowl
    winner          TEXT,
    victory_margin  INTEGER,
    victory_type    TEXT,     -- runs / wickets
    status          TEXT DEFAULT 'completed'  -- live / completed / upcoming
);

-- Innings-level player statistics
-- Stores batting and bowling figures for each player innings.
CREATE TABLE IF NOT EXISTS innings_scores (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER REFERENCES matches(match_id),
    player_id        INTEGER REFERENCES players(player_id),
    innings_no       INTEGER,        -- 1 or 2 (or 1-4 for Tests)
    batting_position  INTEGER,
    runs_scored      INTEGER DEFAULT 0,
    balls_faced      INTEGER DEFAULT 0,
    fours            INTEGER DEFAULT 0,
    sixes            INTEGER DEFAULT 0,
    strike_rate      REAL,
    overs_bowled     REAL DEFAULT 0,
    runs_conceded    INTEGER DEFAULT 0,
    wickets_taken    INTEGER DEFAULT 0,
    economy          REAL,
    catches          INTEGER DEFAULT 0,
    stumpings        INTEGER DEFAULT 0,
    match_date       TEXT             -- Denormalized for date filtering
);

-- Career-level player statistics
-- Stores aggregated batting and bowling performance by format.
CREATE TABLE IF NOT EXISTS player_career_stats (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id          INTEGER REFERENCES players(player_id),
    format             TEXT,     -- Test / ODI / T20I
    matches_played     INTEGER DEFAULT 0,
    runs_scored        INTEGER DEFAULT 0,
    batting_average    REAL,
    strike_rate        REAL,
    hundreds           INTEGER DEFAULT 0,
    fifties            INTEGER DEFAULT 0,
    highest_score     INTEGER,
    wickets_taken      INTEGER DEFAULT 0,
    bowling_average    REAL,
    economy_rate       REAL,
    catches            INTEGER DEFAULT 0,
    stumpings          INTEGER DEFAULT 0,
    UNIQUE(player_id, format)
);

-- Partnership information
-- Stores consecutive batting-position partnerships from Cricsheet data.
CREATE TABLE IF NOT EXISTS partnerships (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id           INTEGER REFERENCES matches(match_id),
    innings_no         INTEGER,
    player1_id         INTEGER REFERENCES players(player_id),
    player2_id         INTEGER REFERENCES players(player_id),
    wicket_number      INTEGER,   -- Which wicket ended the partnership
    partnership_runs   INTEGER
);

-- Match indexes
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_type ON matches(match_type);

-- Innings indexes
CREATE INDEX IF NOT EXISTS idx_innings_player ON innings_scores(player_id);
CREATE INDEX IF NOT EXISTS idx_innings_date ON innings_scores(match_date);

-- Career statistics indexes
CREATE INDEX IF NOT EXISTS idx_career_player ON player_career_stats(player_id);

-- Partnership indexes
CREATE INDEX IF NOT EXISTS idx_partnerships_match ON partnerships(match_id);