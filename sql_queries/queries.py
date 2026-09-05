"""
The 25 SQL practice queries, grouped by difficulty. Each entry is
(title, sql). The SQL Analytics page imports QUERIES and lets the user
pick one from a dropdown, then runs it with utils.db_connection.run_query.

Written for SQLite. Window functions (Q19, 21, 23, 25) need SQLite
3.25+ / Postgres / MySQL 8+ — all fine on any modern install.
"""

QUERIES = {

    # ---------------- BEGINNER ----------------
    "Q1: Indian Players": """
        SELECT
            player_name,
            role AS playing_role,
            batting_style,
            COALESCE(bowling_style, 'N/A') AS bowling_style
        FROM player_roles_admin
        WHERE team = 'India'
        ORDER BY player_name;
    """,

    "Q2: Matches in the last 30 days": """
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
    """,

    "Q3: Top 10 ODI run scorers": """
        SELECT p.player_name, pcs.runs_scored, pcs.batting_average, pcs.hundreds
        FROM player_career_stats pcs
        JOIN players p ON p.player_id = pcs.player_id
        WHERE pcs.format = 'ODI'
        ORDER BY pcs.runs_scored DESC
        LIMIT 10;
    """,

    "Q4: Venues with capacity > 50,000": """
        SELECT venue_name, city, country, capacity
        FROM venues
        WHERE capacity > 50000
        ORDER BY capacity DESC;
    """,

    "Q5: Matches won per team": """
        SELECT m.winner team_name,tc.team_category,tc.competition,tc.country,
            COUNT(*) total_wins
        FROM matches m
        LEFT JOIN team_classification tc ON TRIM(m.winner)=TRIM(tc.team_name)
        WHERE m.winner IS NOT NULL AND TRIM(m.winner)<>''
        GROUP BY m.winner,tc.team_category,tc.competition,tc.country
        ORDER BY total_wins DESC,team_name ASC;
    """,

    "Q6: Player count per role": """
        SELECT
            role,
            COUNT(*) AS player_count
        FROM player_roles_admin
        GROUP BY role
        ORDER BY player_count DESC;
    """,

    "Q7: Highest individual batting score per format": """
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
    """,

    "Q8: Series started in 2024": """
        SELECT series_name,GROUP_CONCAT(DISTINCT host_country) host_country,
            match_type,MIN(match_date) start_date,COUNT(*) total_matches
        FROM "2024_matches"
        WHERE host_country IS NOT NULL AND TRIM(host_country)<>''
        GROUP BY series_name,match_type
        HAVING strftime('%Y',MIN(match_date))='2024'
        ORDER BY MIN(match_date),series_name;
    """,

    # ---------------- INTERMEDIATE ----------------
    "Q9: All-rounders (>1000 runs AND >50 wickets)": """
        SELECT a.player_name,SUM(s.runs_scored) total_runs,
            SUM(s.wickets_taken) total_wickets,'Test, ODI, T20I' format
        FROM player_allrounder_stats s
        JOIN allrounder_player_map a ON a.cricbuzz_player_id=s.cricbuzz_player_id
        WHERE a.actual_role='All-rounder' AND s.format IN ('Test','ODI','T20I')
        GROUP BY a.cricbuzz_player_id,a.player_name
        HAVING SUM(s.runs_scored)>1000 AND SUM(s.wickets_taken)>50
        ORDER BY total_runs DESC;
    """,

    "Q10: Last 20 completed matches": """
        SELECT m.match_id,m.description match_description,
            m.team1 team_1,m.team2 team_2,m.winner winning_team,
            m.victory_margin,m.victory_type,v.venue_name,
            m.match_date,m.result_text status
        FROM matches m
        JOIN venues v ON m.venue_id=v.venue_id
        WHERE m.q10_reference=1
        ORDER BY m.q10_order;
    """,

    "Q11: Compare player performance across formats": """
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
    """,

    "Q12: Home vs away wins per team": """
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
    """,

    "Q13: Partnerships >= 100 runs": """
        SELECT
            format AS match_type,
            partners AS partnership,
            partnership_runs,
            innings_no
        FROM top_partnerships_reference
        WHERE partnership_runs >= 100
        ORDER BY partnership_runs DESC;
    """,

    "Q14: Bowling performance by venue (>=3 matches at venue)": """
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
    """,

    "Q15: Player performance in close matches": """
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
    """,

    "Q16: Yearly batting trend since 2020": """
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
    """,

    # ---------------- ADVANCED ----------------
    "Q17: Toss advantage on match outcome": """
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
    """,

    "Q18: Most economical bowlers (limited-overs)": """
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
    """,

   "Q19: Most consistent batsmen (since 2022)": """
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
    """,

    "Q20: Format-wise match count and average (>=20 total matches)": """
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
    """,

    "Q21: Weighted performance ranking": """
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
    """,

    "Q22: Head-to-head team analysis (last 3 years, >=5 meetings)": """
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
    """,

    "Q23: Recent form & momentum (last 10 innings)": """
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
    """,

    "Q24: Best batting partnerships (>=5 partnerships)": """
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
    """,

    "Q25: Career trajectory (last 6 quarters)": """
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
    """,
}

Q22_VENUE_PERFORMANCE = """
WITH mapped_matches AS (
    SELECT
        TRIM(m.team1) AS team1,
        TRIM(m.team2) AS team2,
        TRIM(m.winner) AS winner,
        v.venue_name,

        CASE
            WHEN LOWER(TRIM(c.actual_batting_first))
                 = LOWER(TRIM(m.team1))
                THEN TRIM(m.team1)

            WHEN LOWER(TRIM(c.actual_batting_first))
                 = LOWER(TRIM(m.team2))
                THEN TRIM(m.team2)

            ELSE NULL
        END AS batting_first_team,

        CASE
            WHEN TRIM(m.team1) < TRIM(m.team2)
                THEN TRIM(m.team1)
            ELSE TRIM(m.team2)
        END AS team_a,

        CASE
            WHEN TRIM(m.team1) < TRIM(m.team2)
                THEN TRIM(m.team2)
            ELSE TRIM(m.team1)
        END AS team_b

    FROM matches m
    JOIN cricsheet_q22_match_details c
        ON c.db_match_id = m.match_id
    JOIN venues v
        ON v.venue_id = m.venue_id

    WHERE date(m.match_date) >= date('now', '-3 years')
      AND m.team1 IS NOT NULL
      AND m.team2 IS NOT NULL
      AND m.winner IS NOT NULL
      AND c.actual_batting_first IS NOT NULL
),

eligible_pairs AS (
    SELECT
        team_a,
        team_b,
        COUNT(*) AS total_matches
    FROM mapped_matches
    GROUP BY
        team_a,
        team_b
    HAVING COUNT(*) >= 5
),

h2h AS (
    SELECT
        mm.*,
        ep.total_matches
    FROM mapped_matches mm
    JOIN eligible_pairs ep
        ON ep.team_a = mm.team_a
       AND ep.team_b = mm.team_b
),

venue_stats AS (
    SELECT
        team_a,
        team_b,
        total_matches,
        venue_name,

        COUNT(*) AS matches_at_venue,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_a))
                    THEN 1
                ELSE 0
            END
        ) AS team_a_batting_first_matches,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_a))
                 AND LOWER(TRIM(winner))
                     = LOWER(TRIM(team_a))
                    THEN 1
                ELSE 0
            END
        ) AS team_a_batting_first_wins,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_b))
                    THEN 1
                ELSE 0
            END
        ) AS team_a_bowling_first_matches,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_b))
                 AND LOWER(TRIM(winner))
                     = LOWER(TRIM(team_a))
                    THEN 1
                ELSE 0
            END
        ) AS team_a_bowling_first_wins,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_b))
                    THEN 1
                ELSE 0
            END
        ) AS team_b_batting_first_matches,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_b))
                 AND LOWER(TRIM(winner))
                     = LOWER(TRIM(team_b))
                    THEN 1
                ELSE 0
            END
        ) AS team_b_batting_first_wins,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_a))
                    THEN 1
                ELSE 0
            END
        ) AS team_b_bowling_first_matches,

        SUM(
            CASE
                WHEN LOWER(TRIM(batting_first_team))
                     = LOWER(TRIM(team_a))
                 AND LOWER(TRIM(winner))
                     = LOWER(TRIM(team_b))
                    THEN 1
                ELSE 0
            END
        ) AS team_b_bowling_first_wins

    FROM h2h

    WHERE batting_first_team IS NOT NULL

    GROUP BY
        team_a,
        team_b,
        total_matches,
        venue_name
)

SELECT
    team_a,
    team_b,
    venue_name,
    matches_at_venue,

    team_a_batting_first_matches,
    team_a_batting_first_wins,

    ROUND(
        100.0 * team_a_batting_first_wins
        / NULLIF(team_a_batting_first_matches, 0),
        1
    ) AS team_a_batting_first_win_pct,

    team_a_bowling_first_matches,
    team_a_bowling_first_wins,

    ROUND(
        100.0 * team_a_bowling_first_wins
        / NULLIF(team_a_bowling_first_matches, 0),
        1
    ) AS team_a_bowling_first_win_pct,

    team_b_batting_first_matches,
    team_b_batting_first_wins,

    ROUND(
        100.0 * team_b_batting_first_wins
        / NULLIF(team_b_batting_first_matches, 0),
        1
    ) AS team_b_batting_first_win_pct,

    team_b_bowling_first_matches,
    team_b_bowling_first_wins,

    ROUND(
        100.0 * team_b_bowling_first_wins
        / NULLIF(team_b_bowling_first_matches, 0),
        1
    ) AS team_b_bowling_first_win_pct

FROM venue_stats

ORDER BY
    total_matches DESC,
    team_a,
    team_b,
    matches_at_venue DESC,
    venue_name
"""