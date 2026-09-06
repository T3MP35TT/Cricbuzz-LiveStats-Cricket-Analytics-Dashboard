# SQL Analytics

## Overview

The SQL Analytics module contains 25 complete cricket analytics queries. The production query source explicitly defines each entry as a `(title, sql)` pair and states that the queries are written for SQLite.

The application loads the query definitions, allows the user to select a challenge, executes it through the database connection layer, and presents the results through the Streamlit analytics interface.

## Difficulty Structure

- **Beginner:** Q1–Q8
- **Intermediate:** Q9–Q16
- **Advanced:** Q17–Q25

## Query Index

| Query | Difficulty | Focus |
|---|---|---|
| Q1 | Beginner | Indian player profiles |
| Q2 | Beginner | Recent matches |
| Q3 | Beginner | ODI run leaders |
| Q4 | Beginner | Large-capacity venues |
| Q5 | Beginner | Team wins |
| Q6 | Beginner | Player roles |
| Q7 | Beginner | Highest score by format |
| Q8 | Beginner | 2024 series |
| Q9 | Intermediate | All-rounder career performance |
| Q10 | Intermediate | Last 20 completed matches |
| Q11 | Intermediate | Cross-format player performance |
| Q12 | Intermediate | Home vs away wins |
| Q13 | Intermediate | 100+ partnerships |
| Q14 | Intermediate | Venue bowling performance |
| Q15 | Intermediate | Close-match player performance |
| Q16 | Intermediate | Yearly batting trends |
| Q17 | Advanced | Toss advantage |
| Q18 | Advanced | Limited-overs economy |
| Q19 | Advanced | Batting consistency |
| Q20 | Advanced | Format-wise match counts and averages |
| Q21 | Advanced | Weighted performance ranking |
| Q22 | Advanced | Head-to-head team analysis |
| Q23 | Advanced | Recent form and momentum |
| Q24 | Advanced | Best batting partnerships |
| Q25 | Advanced | Career trajectory |

## Q1: Indian Players

**Difficulty:** Beginner

### Business Question

Find all players who represent India. Display their full name, playing role, batting style, and bowling style.

### Production SQL

```sql
SELECT
            player_name,
            role AS playing_role,
            batting_style,
            COALESCE(bowling_style, 'N/A') AS bowling_style
        FROM player_roles_admin
        WHERE team = 'India'
        ORDER BY player_name;
```

## Q2: Matches in the last 30 days

**Difficulty:** Beginner

### Business Question

Show all cricket matches that were played in the last 30 days. Include the match description, both team names, venue name with city, and the match date. Sort by most recent matches first.

### Production SQL

```sql
SELECT m.match_id,m.description,m.team1,m.team2,
            COALESCE(SUM(CASE WHEN b.innings_no IN (1,3) THEN b.runs_conceded ELSE 0 END),0) team1_runs,
            COALESCE(SUM(CASE WHEN b.innings_no IN (2,4) THEN b.runs_conceded ELSE 0 END),0) team2_runs,
            COALESCE(SUM(CASE WHEN b.innings_no IN (1,3) THEN b.wickets_taken ELSE 0 END),0) team1_wickets,
            COALESCE(SUM(CASE WHEN b.innings_no IN (2,4) THEN b.wickets_taken ELSE 0 END),0) team2_wickets,
            m.winner winning_team,m.result_text result,m.match_type,
            v.venue_name,v.city,m.match_date
        FROM matches m
        JOIN venues v ON m.venue_id=v.venue_id
        LEFT JOIN cricsheet_bowling_match b ON m.match_id=b.match_id
        WHERE date(m.match_date)>=date('now','-30 day')
        GROUP BY m.match_id
        ORDER BY m.match_date DESC;
```

## Q3: Top 10 ODI run scorers

**Difficulty:** Beginner

### Business Question

List the top 10 highest run scorers in ODI cricket. Show player name, total runs scored, batting average, and number of centuries. Display the highest run scorer first.

### Production SQL

```sql
SELECT p.player_name, pcs.runs_scored, pcs.batting_average, pcs.hundreds
        FROM player_career_stats pcs
        JOIN players p ON p.player_id = pcs.player_id
        WHERE pcs.format = 'ODI'
        ORDER BY pcs.runs_scored DESC
        LIMIT 10;
```

## Q4: Venues with capacity > 50,000

**Difficulty:** Beginner

### Business Question

Display all cricket venues that have a seating capacity of more than 50,000 spectators. Show venue name, city, country, and capacity. Order by largest capacity first.

### Production SQL

```sql
SELECT venue_name, city, country, capacity
        FROM venues
        WHERE capacity > 50000
        ORDER BY capacity DESC;
```

## Q5: Matches won per team

**Difficulty:** Beginner

### Business Question

Calculate how many matches each team has won. Show team name and total number of wins. Display teams with most wins first.

### Production SQL

```sql
SELECT m.winner team_name,tc.team_category,tc.competition,tc.country,
            COUNT(*) total_wins
        FROM matches m
        LEFT JOIN team_classification tc ON TRIM(m.winner)=TRIM(tc.team_name)
        WHERE m.winner IS NOT NULL AND TRIM(m.winner)<>''
        GROUP BY m.winner,tc.team_category,tc.competition,tc.country
        ORDER BY total_wins DESC,team_name ASC;
```

## Q6: Player count per role

**Difficulty:** Beginner

### Business Question

Count how many players belong to each playing role (like Batsman, Bowler, All-rounder, Wicket-keeper). Show the role and count of players for each role.

### Production SQL

```sql
SELECT
            role,
            COUNT(*) AS player_count
        FROM player_roles_admin
        GROUP BY role
        ORDER BY player_count DESC;
```

## Q7: Highest individual batting score per format

**Difficulty:** Beginner

### Business Question

Find the highest individual batting score achieved in each cricket format (Test, ODI, T20I). Display the format and the highest score for that format.

### Production SQL

```sql
SELECT format,player_name,highest_score
        FROM (
            SELECT CASE WHEN m.match_type='IT20' THEN 'T20I' ELSE m.match_type END format,
                p.player_name,i.runs_scored highest_score,
                ROW_NUMBER() OVER (
                    PARTITION BY m.match_type
                    ORDER BY i.runs_scored DESC,p.player_name
                ) rn
            FROM innings_scores i
            JOIN matches m ON m.match_id=i.match_id
            JOIN players p ON p.player_id=i.player_id
            WHERE m.match_type IN ('Test','ODI','IT20')
        )
        WHERE rn=1
        ORDER BY CASE format WHEN 'Test' THEN 1 WHEN 'ODI' THEN 2 WHEN 'T20I' THEN 3 END;
```

## Q8: Series started in 2024

**Difficulty:** Beginner

### Business Question

Show all cricket series that started in the year 2024. Include series name, host country, match type, start date, and total number of matches planned.

### Production SQL

```sql
SELECT series_name,GROUP_CONCAT(DISTINCT host_country) host_country,
            match_type,MIN(match_date) start_date,COUNT(*) total_matches
        FROM "2024_matches"
        WHERE host_country IS NOT NULL AND TRIM(host_country)<>''
        GROUP BY series_name,match_type
        HAVING strftime('%Y',MIN(match_date))='2024'
        ORDER BY MIN(match_date),series_name;
```

## Q9: All-rounders (>1000 runs AND >50 wickets)

**Difficulty:** Intermediate

### Business Question

Find all-rounder players who have scored more than 1000 runs AND taken more than 50 wickets in their career. Display player name, total runs, total wickets, and the cricket format.

### Production SQL

```sql
SELECT a.player_name,SUM(s.runs_scored) total_runs,
            SUM(s.wickets_taken) total_wickets,'Test, ODI, T20I' format
        FROM player_allrounder_stats s
        JOIN allrounder_player_map a ON a.cricbuzz_player_id=s.cricbuzz_player_id
        WHERE a.actual_role='All-rounder' AND s.format IN ('Test','ODI','T20I')
        GROUP BY a.cricbuzz_player_id,a.player_name
        HAVING SUM(s.runs_scored)>1000 AND SUM(s.wickets_taken)>50
        ORDER BY total_runs DESC;
```

## Q10: Last 20 completed matches

**Difficulty:** Intermediate

### Business Question

Get details of the last 20 completed matches. Show match description, both team names, winning team, victory margin, victory type (runs/wickets), and venue name. Display most recent matches first.

### Production SQL

```sql
SELECT m.match_id,m.description match_description,
            m.team1 team_1,m.team2 team_2,m.winner winning_team,
            m.victory_margin,m.victory_type,v.venue_name,
            m.match_date,m.result_text status
        FROM matches m
        JOIN venues v ON m.venue_id=v.venue_id
        WHERE m.q10_reference=1
        ORDER BY m.q10_order;
```

## Q11: Compare player performance across formats

**Difficulty:** Intermediate

### Business Question

Compare each player's performance across different cricket formats. For players who have played at least 2 different formats, show their total runs in Test cricket, ODI cricket, and T20I cricket, along with their overall batting average across all formats.

### Production SQL

```sql
SELECT
            p.player_name,
            SUM(CASE WHEN pcs.format = 'Test' THEN pcs.runs_scored ELSE 0 END) AS test_runs,
            SUM(CASE WHEN pcs.format = 'ODI' THEN pcs.runs_scored ELSE 0 END) AS odi_runs,
            SUM(CASE WHEN pcs.format IN ('T20I', 'IT20') THEN pcs.runs_scored ELSE 0 END) AS t20i_runs,
            ROUND(AVG(pcs.batting_average), 2) AS overall_avg
        FROM player_career_stats pcs
        JOIN players p ON p.player_id = pcs.player_id
        GROUP BY p.player_id, p.player_name
        HAVING test_runs > 0 AND odi_runs > 0 AND t20i_runs > 0
        ORDER BY test_runs DESC;
```

## Q12: Home vs away wins per team

**Difficulty:** Intermediate

### Business Question

Analyze each international team's performance when playing at home versus playing away. Determine whether each team played at home or away based on whether the venue country matches the team's country. Count wins for each team in both home and away conditions.

### Production SQL

```sql
SELECT team,
            SUM(is_home AND winner=team) home_wins,
            SUM(NOT is_home AND winner=team) away_wins
        FROM (
            SELECT m.team1 team,m.winner,v.country=m.team1 is_home
            FROM matches m JOIN venues v ON m.venue_id=v.venue_id
            UNION ALL
            SELECT m.team2,m.winner,v.country=m.team2
            FROM matches m JOIN venues v ON m.venue_id=v.venue_id
        )
        GROUP BY team
        ORDER BY home_wins DESC;
```

## Q13: Partnerships >= 100 runs

**Difficulty:** Intermediate

### Business Question

Identify batting partnerships where two consecutive batsmen (batting positions next to each other) scored a combined total of 100 or more runs in the same innings. Show both player names, their combined partnership runs, and which innings it occurred in.

### Production SQL

```sql
SELECT
            format AS match_type,
            partners AS partnership,
            partnership_runs,
            innings_no
        FROM top_partnerships_reference
        WHERE partnership_runs >= 100
        ORDER BY partnership_runs DESC;
```

## Q14: Bowling performance by venue (>=3 matches at venue)

**Difficulty:** Intermediate

### Business Question

Examine bowling performance at different venues. For bowlers who have played at least 3 matches at the same venue, calculate their average economy rate, total wickets taken, and number of matches played at each venue. Focus on bowlers who bowled at least 4 overs in each match.

### Production SQL

```sql
WITH q AS (
            SELECT player_name
            FROM cricsheet_bowling_match
            GROUP BY player_name,strftime('%Y',match_date),
                    (CAST(strftime('%m',match_date) AS INT)-1)/3
            HAVING COUNT(DISTINCT match_id)>=3
        )
        SELECT b.player_name,b.venue_name,
            ROUND(SUM(b.runs_conceded)/(SUM(b.balls_bowled)/6.0),2) avg_economy,
            SUM(b.wickets_taken) total_wickets,
            COUNT(DISTINCT b.match_id) matches_played
        FROM cricsheet_bowling_match b
        WHERE b.player_name IN (
            SELECT player_name FROM q GROUP BY player_name HAVING COUNT(*)>=6
        )
        GROUP BY b.player_name,b.venue_name
        HAVING COUNT(DISTINCT b.match_id)>=3
        AND SUM(b.balls_bowled)>=72
        ORDER BY avg_economy;
```

## Q15: Player performance in close matches

**Difficulty:** Intermediate

### Business Question

Identify players who perform exceptionally well in close matches. A close match is defined as one decided by less than 50 runs OR less than 5 wickets. For these close matches, calculate each player's average runs scored, total close matches played, and how many of those close matches their team won when they batted.

### Production SQL

```sql
WITH q AS(SELECT player_id FROM innings_scores i JOIN matches m ON m.match_id=i.match_id
    WHERE m.match_type IN('Test','ODI','IT20') GROUP BY player_id,strftime('%Y',m.match_date),(CAST(strftime('%m',m.match_date) AS INT)-1)/3
    HAVING COUNT(DISTINCT m.match_id)>=3),x AS(SELECT i.player_id,i.match_id,SUM(i.runs_scored) runs,
    CASE WHEN MIN(i.innings_no) IN(1,3) THEN m.team1 ELSE m.team2 END team,m.winner
    FROM innings_scores i JOIN matches m ON m.match_id=i.match_id
    WHERE m.match_type IN('Test','ODI','IT20') AND m.winner IS NOT NULL
    AND((m.victory_type='runs' AND m.victory_margin<50)OR(m.victory_type='wickets' AND m.victory_margin<5))
    AND i.player_id IN(SELECT player_id FROM q GROUP BY player_id HAVING COUNT(*)>=6)
    GROUP BY i.player_id,i.match_id)
    SELECT p.player_name,ROUND(AVG(x.runs),2) avg_runs_close_matches,COUNT(*) close_matches_played,
    SUM(x.team=x.winner) close_matches_team_won
    FROM x JOIN players p ON p.player_id=x.player_id
    GROUP BY x.player_id,p.player_name ORDER BY avg_runs_close_matches DESC;
```

## Q16: Yearly batting trend since 2020

**Difficulty:** Intermediate

### Business Question

Track how players' batting performance changes over different years. For matches since 2020, show each player's average runs per match and average strike rate for each year. Only include players who played at least 5 matches in that year.

### Production SQL

```sql
WITH q AS(
    SELECT player_id FROM innings_scores i JOIN matches m ON m.match_id=i.match_id
    WHERE m.match_date>='2020-01-01'
    GROUP BY player_id,strftime('%Y',m.match_date),(CAST(strftime('%m',m.match_date) AS INT)-1)/3
    HAVING COUNT(DISTINCT m.match_id)>=3
    ),e AS(
    SELECT player_id FROM q GROUP BY player_id HAVING COUNT(*)>=6
    ),y AS(
    SELECT i.player_id,strftime('%Y',m.match_date) year,i.match_id,SUM(i.runs_scored) runs,AVG(i.strike_rate) sr
    FROM innings_scores i JOIN matches m ON m.match_id=i.match_id JOIN e ON e.player_id=i.player_id
    WHERE m.match_date>='2020-01-01' GROUP BY i.player_id,year,i.match_id
    ),p AS(
    SELECT player_id FROM y GROUP BY player_id
    HAVING SUM(year='2020')>=5 AND SUM(year='2021')>=5 AND SUM(year='2022')>=5
    AND SUM(year='2023')>=5 AND SUM(year='2024')>=5 AND SUM(year='2025')>=5 AND SUM(year='2026')>=5
    ),t AS(
    SELECT player_id,AVG(CASE WHEN year='2026' THEN runs END)-AVG(CASE WHEN year='2020' THEN runs END) change
    FROM y JOIN p USING(player_id) GROUP BY player_id
    )
    SELECT pl.player_name,y.year,ROUND(AVG(y.runs),2) avg_runs,ROUND(AVG(y.sr),2) avg_strike_rate,
    CASE WHEN t.change>2 THEN '↗ Improving' WHEN t.change<-2 THEN '↘ Declining' ELSE '→ Stable' END trend
    FROM y JOIN p USING(player_id) JOIN t USING(player_id) JOIN players pl USING(player_id)
    GROUP BY y.player_id,pl.player_name,y.year;
```

## Q17: Toss advantage on match outcome

**Difficulty:** Advanced

### Business Question

Investigate whether winning the toss gives teams an advantage in winning matches. Calculate what percentage of matches are won by the team that wins the toss, broken down by their toss decision (choosing to bat first or bowl first).

### Production SQL

```sql
WITH clean AS (
            SELECT LOWER(TRIM(toss_decision)) toss_decision,toss_winner,winner
            FROM matches
            WHERE toss_winner IS NOT NULL AND TRIM(toss_winner)<>''
            AND winner IS NOT NULL AND TRIM(winner)<>''
            AND toss_decision IS NOT NULL
            AND LOWER(TRIM(toss_decision)) IN ('bat','bowl')
        ),
        stats AS (
            SELECT toss_decision,
                ROUND(100.0*SUM(
                    CASE WHEN LOWER(TRIM(toss_winner))=LOWER(TRIM(winner))
                            THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),2) win_pct
            FROM clean
            GROUP BY toss_decision
        ),
        ranked AS (
            SELECT *,RANK() OVER(ORDER BY win_pct DESC) advantage_rank
            FROM stats
        )
        SELECT toss_decision,
            win_pct AS win_pct_after_winning_toss
        FROM ranked
        ORDER BY advantage_rank,toss_decision;
```

## Q18: Most economical bowlers (limited-overs)

**Difficulty:** Advanced

### Business Question

Find the most economical bowlers in limited-overs cricket (ODI and T20 formats). Calculate each bowler's overall economy rate and total wickets taken. Only consider bowlers who have bowled in at least 10 matches and bowled at least 2 overs per match on average.

### Production SQL

```sql
WITH clean_bowling AS (
        SELECT
            b.cricbuzz_player_id,
            b.economy_rate,
            b.wickets_taken,
            b.format,
            b.matches_played,
            b.bowling_balls
        FROM player_bowling_stats b
        WHERE b.format IN ('ODI', 'T20I')
        AND b.matches_played >= 10
        AND b.bowling_balls IS NOT NULL
        AND b.matches_played IS NOT NULL
        AND 1.0 * b.bowling_balls / NULLIF(b.matches_played, 0) >= 12
        AND b.economy_rate IS NOT NULL
        AND b.economy_rate >= 0
        AND b.wickets_taken IS NOT NULL
    ),

    validated AS (
        SELECT
            cb.*,
            pr.player_name
        FROM clean_bowling cb
        JOIN player_roles_reference pr
            ON cb.cricbuzz_player_id = pr.player_id
        WHERE pr.player_name IS NOT NULL
        AND TRIM(pr.player_name) <> ''
    ),

    ranked AS (
        SELECT
            player_name,
            ROUND(economy_rate, 2) AS economy_rate,
            wickets_taken,
            format,
            RANK() OVER (
                PARTITION BY format
                ORDER BY economy_rate ASC, wickets_taken DESC
            ) AS economy_rank
        FROM validated
    )

    SELECT
        player_name,
        economy_rate,
        wickets_taken,
        format
    FROM ranked
    WHERE economy_rank <= 20
    ORDER BY economy_rate ASC,
            wickets_taken DESC,
            player_name;
```

## Q19: Most consistent batsmen (since 2022)

**Difficulty:** Advanced

### Business Question

Determine which batsmen are most consistent in their scoring. Calculate the average runs scored and the standard deviation of runs for each player. Only include players who have faced at least 10 balls per innings and played since 2022. A lower standard deviation indicates more consistent performance.

### Production SQL

```sql
WITH innings AS (
        SELECT
            player_id,
            match_id,
            innings_no,
            SUM(runs_scored) runs
        FROM innings_scores
        WHERE date(match_date) >= '2022-01-01'
        AND runs_scored IS NOT NULL
        AND balls_faced IS NOT NULL
        GROUP BY player_id, match_id, innings_no
        HAVING SUM(balls_faced) >= 10
    ),
    stats AS (
        SELECT
            p.player_id,
            p.player_name,
            AVG(i.runs) avg_runs,
            SQRT(MAX(0, AVG(i.runs*i.runs)-AVG(i.runs)*AVG(i.runs))) stddev_runs
        FROM innings i
        JOIN players p ON p.player_id = i.player_id
        WHERE p.admin_active = 1
        AND p.player_name IS NOT NULL
        GROUP BY p.player_id, p.player_name
        HAVING COUNT(*) >= 5
    )
    SELECT
        player_name,
        ROUND(avg_runs,2) avg_runs,
        ROUND(stddev_runs,2) stddev_runs
    FROM stats
    ORDER BY stddev_runs ASC, avg_runs DESC;
```

## Q20: Format-wise match count and average (>=20 total matches)

**Difficulty:** Advanced

### Business Question

Analyze how many matches each player has played in different cricket formats and their batting average in each format. Show the count of Test matches, ODI matches, and T20 matches for each player, along with their respective batting averages. Only include players who have played at least 20 total matches across all formats.

### Production SQL

```sql
WITH s AS (
        SELECT
            p.player_id,p.player_name,
            SUM(CASE WHEN pcs.format='Test' THEN pcs.matches_played ELSE 0 END) test_matches,
            SUM(CASE WHEN pcs.format='ODI' THEN pcs.matches_played ELSE 0 END) odi_matches,
            SUM(CASE WHEN pcs.format IN('T20I','IT20') THEN pcs.matches_played ELSE 0 END) t20i_matches,
            AVG(CASE WHEN pcs.format='Test' THEN pcs.batting_average END) test_avg,
            AVG(CASE WHEN pcs.format='ODI' THEN pcs.batting_average END) odi_avg,
            AVG(CASE WHEN pcs.format IN('T20I','IT20') THEN pcs.batting_average END) t20i_avg
        FROM player_career_stats pcs
        JOIN players p ON p.player_id=pcs.player_id
        WHERE p.admin_active=1
        AND p.player_name IS NOT NULL
        AND pcs.matches_played IS NOT NULL
        GROUP BY p.player_id,p.player_name
        HAVING SUM(pcs.matches_played)>=20
    ),
    r AS (
        SELECT *,test_matches+odi_matches+t20i_matches total_matches,
            RANK() OVER(ORDER BY test_matches+odi_matches+t20i_matches DESC) rank_no
        FROM s
    )
    SELECT
        player_name,test_matches,odi_matches,t20i_matches,
        test_avg,odi_avg,t20i_avg,total_matches,rank_no
    FROM r
    ORDER BY rank_no,player_name;
```

## Q21: Weighted performance ranking

**Difficulty:** Advanced

### Business Question

Create a comprehensive performance ranking system for players. Combine their batting performance (runs scored, batting average, strike rate), bowling performance (wickets taken, bowling average, economy rate), and fielding performance (catches, stumpings) into a single weighted score. Use this formula:
- Batting points: (runs_scored × 0.01) + (batting_average × 0.5) + (strike_rate × 0.3)
- Bowling points: (wickets_taken × 2) + ((50 - bowling_average) × 0.5) + ((6 - economy_rate) × 2)
- Fielding points: (catches × 3) + (stumpings × 5)
Rank the top performers in each cricket format.

### Production SQL

```sql
WITH s AS (
        SELECT p.player_name,
            CASE WHEN pcs.format='IT20' THEN 'T20I' ELSE pcs.format END format,
            COALESCE(pcs.runs_scored,0)*.01+
            COALESCE(pcs.batting_average,0)*.5+
            COALESCE(pcs.strike_rate,0)*.3+
            COALESCE(pcs.wickets_taken,0)*2+
            (50-COALESCE(pcs.bowling_average,50))*.5+
            (6-COALESCE(pcs.economy_rate,6))*2+
            COALESCE(pcs.catches,0)*3+
            COALESCE(pcs.stumpings,0)*5 score
        FROM player_career_stats pcs
        JOIN players p ON p.player_id=pcs.player_id
        WHERE p.admin_active=1
        AND p.player_name IS NOT NULL
        AND TRIM(p.player_name)<>''
        AND pcs.format IN('Test','ODI','T20I','IT20')
    ),
    r AS (
        SELECT *,ROUND(score,2) score,
            ROW_NUMBER() OVER(PARTITION BY format ORDER BY score DESC) rank
        FROM s
        WHERE score>0
    )
    SELECT rank,player_name,format,score
    FROM r
    ORDER BY CASE format WHEN 'Test' THEN 1 WHEN 'ODI' THEN 2 ELSE 3 END,rank;
```

## Q22: Head-to-head team analysis (last 3 years, >=5 meetings)

**Difficulty:** Advanced

### Business Question

Build a head-to-head match prediction analysis between teams. For each pair of teams that have played at least 5 matches against each other in the last 3 years, calculate:
- Total matches played between them
- Wins for each team
- Average victory margin when each team wins
- Performance when batting first vs bowling first at different venues
- Overall win percentage for each team in this head-to-head record

### Production SQL

```sql
WITH m AS (
    SELECT
    MIN(TRIM(m.team1),TRIM(m.team2)) team_a,
    MAX(TRIM(m.team1),TRIM(m.team2)) team_b,
    TRIM(m.winner) winner,m.victory_margin
    FROM matches m
    JOIN cricsheet_q22_match_details c ON c.db_match_id=m.match_id
    WHERE date(m.match_date)>=date('now','-3 years')
    AND m.team1 IS NOT NULL AND TRIM(m.team1)<>''
    AND m.team2 IS NOT NULL AND TRIM(m.team2)<>''
    AND m.winner IS NOT NULL AND TRIM(m.winner)<>''
    AND c.actual_batting_first IS NOT NULL
    ),
    r AS (
    SELECT
    team_a,team_b,COUNT(*) total_matches,
    SUM(LOWER(winner)=LOWER(team_a)) team_a_wins,
    SUM(LOWER(winner)=LOWER(team_b)) team_b_wins,
    AVG(CASE WHEN LOWER(winner)=LOWER(team_a)
                THEN victory_margin END) team_a_avg_victory_margin,
    AVG(CASE WHEN LOWER(winner)=LOWER(team_b)
                THEN victory_margin END) team_b_avg_victory_margin,
    RANK() OVER(ORDER BY COUNT(*) DESC) match_rank
    FROM m
    GROUP BY team_a,team_b
    HAVING COUNT(*)>=5
    )
    SELECT
    team_a,team_b,total_matches,team_a_wins,team_b_wins,
    ROUND(100.0*team_a_wins/NULLIF(total_matches,0),1) team_a_win_percentage,
    ROUND(100.0*team_b_wins/NULLIF(total_matches,0),1) team_b_win_percentage,
    ROUND(team_a_avg_victory_margin,1) team_a_avg_victory_margin,
    ROUND(team_b_avg_victory_margin,1) team_b_avg_victory_margin
    FROM r
    ORDER BY total_matches DESC,team_a,team_b;
```

## Q23: Recent form & momentum (last 10 innings)

**Difficulty:** Advanced

### Business Question

Analyze recent player form and momentum. For each player's last 10 batting performances, calculate:
- Average runs in their last 5 matches vs their last 10 matches
- Recent strike rate trends
- Number of scores above 50 in recent matches
- A consistency score based on standard deviation
Based on these metrics, categorize players as being in "Excellent Form", "Good Form", "Average Form", or "Poor Form".

### Production SQL

```sql
WITH r AS (
    SELECT i.player_id,COALESCE(NULLIF(TRIM(p.real_name),''),p.player_name) player_name,
    i.runs_scored,i.strike_rate,ROW_NUMBER() OVER(PARTITION BY i.player_id ORDER BY date(i.match_date) DESC,i.id DESC) rn
    FROM Q23_batting_innings_SR i JOIN players p ON p.player_id=i.player_id
    WHERE p.admin_active=1 AND i.runs_scored IS NOT NULL AND i.strike_rate IS NOT NULL AND i.match_date IS NOT NULL
    ),
    s AS (
    SELECT player_id,player_name,
    AVG(CASE WHEN rn<=5 THEN runs_scored END) avg_last_5,AVG(runs_scored) avg_last_10,
    AVG(CASE WHEN rn<=5 THEN strike_rate END) strike_rate_last_5,AVG(strike_rate) strike_rate_last_10,
    SUM(runs_scored>=50) scores_50_plus,
    SQRT(MAX(0,AVG(runs_scored*runs_scored)-AVG(runs_scored)*AVG(runs_scored))) stddev_runs
    FROM r WHERE rn<=10 GROUP BY player_id,player_name HAVING COUNT(*)>=5
    )
    SELECT player_name,ROUND(avg_last_5,2) avg_last_5,ROUND(avg_last_10,2) avg_last_10,
    ROUND(strike_rate_last_5,2) strike_rate_last_5,ROUND(strike_rate_last_10,2) strike_rate_last_10,
    ROUND(strike_rate_last_5-strike_rate_last_10,2) strike_rate_trend,scores_50_plus,
    ROUND(stddev_runs,2) stddev_runs,
    ROUND(100.0*avg_last_10/(avg_last_10+COALESCE(stddev_runs,0)),1) consistency_score,
    CASE WHEN avg_last_5>=50 AND 100.0*avg_last_10/(avg_last_10+COALESCE(stddev_runs,0))>=50
    AND (avg_last_5>=avg_last_10*1.1 OR strike_rate_last_5-strike_rate_last_10>=10) THEN 'Excellent Form'
    WHEN avg_last_5>=30 AND 100.0*avg_last_10/(avg_last_10+COALESCE(stddev_runs,0))>=45 THEN 'Good Form'
    WHEN avg_last_5>=15 AND 100.0*avg_last_10/(avg_last_10+COALESCE(stddev_runs,0))>=30 THEN 'Average Form'
    ELSE 'Poor Form' END form_category
    FROM s
    ORDER BY CASE form_category WHEN 'Excellent Form' THEN 1 WHEN 'Good Form' THEN 2 WHEN 'Average Form' THEN 3 ELSE 4 END,avg_last_5 DESC;
```

## Q24: Best batting partnerships (>=5 partnerships)

**Difficulty:** Advanced

### Business Question

Study successful batting partnerships to identify the best player combinations. For pairs of players who have batted together as consecutive batsmen (positions differ by 1) in at least 5 partnerships:
- Calculate their average partnership runs
- Count how many of their partnerships exceeded 50 runs
- Find their highest partnership score
- Calculate their success rate (percentage of good partnerships)
Rank the most successful batting partnerships.

### Production SQL

```sql
WITH s AS (
    SELECT p1.player_name batter_1,p2.player_name batter_2,
            COUNT(*) partnerships_played,AVG(pt.partnership_runs) avg_partnership_runs,
            SUM(pt.partnership_runs>50) partnerships_over_50,
            MAX(pt.partnership_runs) highest_partnership
    FROM partnerships pt
    JOIN players p1 ON p1.player_id=pt.player1_id
    JOIN players p2 ON p2.player_id=pt.player2_id
    WHERE p1.admin_active=1 AND p2.admin_active=1
    AND pt.partnership_runs IS NOT NULL
    AND pt.partnership_runs>=0
    GROUP BY pt.player1_id,pt.player2_id
    HAVING COUNT(*)>=5
    ),
    r AS (
    SELECT *,ROUND(100.0*partnerships_over_50/partnerships_played,2) success_rate_pct,
            RANK() OVER(ORDER BY avg_partnership_runs DESC) partnership_rank
    FROM s
    )
    SELECT batter_1,batter_2,partnerships_played,
        ROUND(avg_partnership_runs,2) avg_partnership_runs,
        partnerships_over_50,highest_partnership,success_rate_pct
    FROM r
    ORDER BY partnership_rank;
```

## Q25: Career trajectory (last 6 quarters)

**Difficulty:** Advanced

### Business Question

Perform a time-series analysis of player performance evolution. Track how each player's batting performance changes over time by:
- Calculating quarterly averages for runs and strike rate
- Comparing each quarter's performance to the previous quarter
- Identifying whether performance is improving, declining, or stable
- Determining overall career trajectory over the last few years
- Categorizing players' career phase as "Career Ascending", "Career Declining", or "Career Stable"
Only analyze players with data spanning at least 6 quarters and a minimum of 3 matches per quarter.

### Production SQL

```sql
WITH q AS (
    SELECT i.player_id,p.player_name,
            strftime('%Y',i.match_date)||'-Q'||((CAST(strftime('%m',i.match_date) AS INT)-1)/3+1) quarter,
            AVG(i.runs_scored) runs,AVG(i.strike_rate) sr
    FROM innings_scores i JOIN players p ON p.player_id=i.player_id
    WHERE p.admin_active=1 AND i.match_date IS NOT NULL
    AND i.runs_scored IS NOT NULL AND i.strike_rate IS NOT NULL
    GROUP BY i.player_id,quarter HAVING COUNT(DISTINCT i.match_id)>=3
    ),
    x AS (
    SELECT player_id,player_name,
            MAX(CASE WHEN quarter='2025-Q1' THEN runs END) first_runs,
            MAX(CASE WHEN quarter='2026-Q2' THEN runs END) last_runs,
            MAX(CASE WHEN quarter='2025-Q1' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q1,
            MAX(CASE WHEN quarter='2025-Q2' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q2,
            MAX(CASE WHEN quarter='2025-Q3' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q3,
            MAX(CASE WHEN quarter='2025-Q4' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q4,
            MAX(CASE WHEN quarter='2026-Q1' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q5,
            MAX(CASE WHEN quarter='2026-Q2' THEN ROUND(runs,2)||' / '||ROUND(sr,2) END) q6
    FROM q WHERE quarter BETWEEN '2025-Q1' AND '2026-Q2'
    GROUP BY player_id,player_name
    HAVING COUNT(*)=6
    )
    SELECT player_name,
    q1 "2025-Q1 (Avg Runs/SR)",q2 "2025-Q2 (Avg Runs/SR)",
    q3 "2025-Q3 (Avg Runs/SR)",q4 "2025-Q4 (Avg Runs/SR)",
    q5 "2026-Q1 (Avg Runs/SR)",q6 "2026-Q2 (Avg Runs/SR)",
    CASE WHEN last_runs>first_runs*1.1 THEN 'Career Ascending'
        WHEN last_runs<first_runs*.9 THEN 'Career Declining'
        ELSE 'Career Stable' END career_phase
    FROM x
    ORDER BY CASE WHEN last_runs>first_runs*1.1 THEN 1
                WHEN last_runs<first_runs*.9 THEN 3 ELSE 2 END,player_name;
```

## Advanced Query Notes

### Q17 — Toss Advantage

The production query cleans toss decision values, compares the toss winner with the match winner, calculates win percentage by toss decision, and ranks the two decisions by observed win percentage.

### Q18 — Economy

The production query considers ODI and T20I records, requires at least 10 matches, and requires an average of at least 12 bowling balls per match, equivalent to 2 overs per match.

### Q19 — Consistency

The production implementation aggregates innings since 2022 where at least 10 balls were faced, then calculates average runs and a population-style standard deviation using the available SQLite expression.

### Q20 — Format Comparison

The production implementation aggregates Test, ODI, and T20I/IT20 match counts and batting averages, then requires at least 20 total matches.

### Q21 — Weighted Ranking

The production implementation applies the requested weighted scoring formula and ranks records by format.

### Q22 — Head-to-Head

The production implementation restricts matches to the last three years, requires at least five meetings per pair, calculates wins and average victory margins, and uses `cricsheet_q22_match_details` for batting-first information. A separate Q22 venue-performance query is also maintained in the production source.

### Q23 — Momentum

The production implementation uses the last ten batting innings available per active player, compares the last five against the last ten, calculates strike-rate trend, 50+ scores, standard deviation, consistency score, and form category.

### Q24 — Partnerships

The production implementation groups partnership records by player pair, requires at least five partnerships, calculates average partnership runs, 50+ partnership count, highest partnership, and success rate.

### Q25 — Career Trajectory

The production implementation groups innings into calendar quarters, requires at least three matches per quarter, and currently evaluates a six-quarter window from 2025-Q1 through 2026-Q2. It classifies the trajectory based on the change between the first and last quarter in that window.

## Query Execution

The analytics workflow is:

```text
Select Q1–Q25
      ↓
Load predefined SQL
      ↓
Execute against SQLite
      ↓
Return DataFrame
      ↓
Display results
      ↓
Build query-specific insights
      ↓
Display interactive analytics
      ↓
Allow CSV export where supported
```

## SQL Safety

The analytics query layer should remain a controlled set of predefined analytical queries. It should not be treated as an unrestricted SQL console.

Destructive operations such as `DROP`, `DELETE`, `UPDATE`, and unrestricted `ALTER` statements should not be exposed through the analytics runner.

## Source of Truth

The production query definitions in the uploaded query source are the source of truth for the SQL shown in this document. Any future query change should update both the production query file and this documentation.
