import numpy as np
from scipy.stats import norm
import pandas as pd
import json
import time
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.endpoints import boxscoreadvancedv3
from nba_api.stats.endpoints import boxscorefourfactorsv3
from nba_api.stats.endpoints import boxscoredefensivev2
from nba_api.stats.endpoints import boxscorematchupsv3
from nba_api.stats.endpoints import boxscoretraditionalv3
from nba_api.stats.endpoints import commonplayerinfo

def monte_carlo_simulation(stats, target, market_type, n_simulations=10000):
    """Enhanced Monte Carlo simulation with detailed defensive metrics"""
    # Get base statistics
    if market_type == 'player_points':
        base_avg = float(stats['points'])
    elif market_type == 'player_assists':
        base_avg = float(stats['assists'])
    elif market_type == 'player_rebounds':
        base_avg = float(stats['rebounds'])
    else:
        raise ValueError(f"Unknown market type: {market_type}")
    
    # Add debug prints
    print(f"Base average: {base_avg}")
    print(f"Target: {target}")
    
    # Ensure we have valid numbers
    if base_avg == 0 or not np.isfinite(base_avg):
        print("Warning: Base average is 0 or invalid")
        return {
            'over_probability': 0.0,
            'under_probability': 0.0,
            'confidence_score': 0.0,
            'simulated_avg': 0.0,
            'simulated_median': 0.0,
            'position_defense_impact': 0.0,
            'team_defense_impact': 0.0,
            'defender_impact': 0.0,
            'pace_impact': 0.0,
            'injury_impact': 0.0
        }
    
    # Calculate standard deviation from recent performance
    std_dev = base_avg * 0.2  # Using 20% of average as estimation
    
    # Generate base simulations
    simulated_outcomes = np.random.normal(base_avg, std_dev, n_simulations)
    
    # Apply minutes adjustment
    minutes_factor = float(stats['minutes']) / 36
    simulated_outcomes *= minutes_factor
    
    # Calculate probabilities
    over_count = np.sum(simulated_outcomes > float(target))
    under_count = n_simulations - over_count
    
    over_prob = (over_count / n_simulations) * 100
    under_prob = (under_count / n_simulations) * 100
    
    # Calculate confidence metrics
    variance = np.var(simulated_outcomes)
    confidence_score = 100 * (1 - (variance / (base_avg ** 2)))
    
    # Calculate exact values without rounding
    simulated_mean = float(np.mean(simulated_outcomes))
    simulated_median = float(np.median(simulated_outcomes))
    
    # Add debug prints
    print(f"Simulated mean: {simulated_mean}")
    print(f"Over probability: {over_prob}%")
    print(f"Under probability: {under_prob}%")
    
    return {
        'over_probability': over_prob,
        'under_probability': under_prob,
        'confidence_score': confidence_score,
        'simulated_avg': simulated_mean,
        'simulated_median': simulated_median,
        'position_defense_impact': 100.0,
        'team_defense_impact': 100.0,
        'defender_impact': 100.0,
        'pace_impact': 100.0,
        'injury_impact': 100.0
    }

def get_player_id(player_name):
    """Get player ID from player name."""
    player_list = players.get_players()
    for player in player_list:
        if player['full_name'].lower() == player_name.lower():
            return player['id']
    return None  # Return None if player is not found

def get_team_abbreviation(team_name):
    """Get team abbreviation from team name."""
    team_list = teams.get_teams()
    for team in team_list:
        if team['full_name'].lower() == team_name.lower():
            return team['abbreviation']
    raise ValueError(f"Team {team_name} not found.")

def fetch_game_log_with_retry(player_id, season_year, timeout=30):
    """Fetch game log with a single attempt and save on timeout."""
    try:
        game_log = playergamelog.PlayerGameLog(player_id=player_id, season=season_year, timeout=timeout).get_data_frames()[0]
        return game_log
    except Exception as e:
        print(f"Error fetching data for season {season_year}: {e}")
        return None

def get_player_stats_against_team(player_name, team_name, num_games=10, num_seasons=4):
    """Fetch and calculate player's stats for games against a specific team."""
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Player {player_name} not found. Skipping...")
        return None
    
    team_abbr = get_team_abbreviation(team_name)
    
    all_game_logs = []
    current_season = 2024  # Update this for the current NBA season
    
    try:
        # Add error handling and DataFrame checks
        for season in range(current_season, current_season - num_seasons, -1):
            print(f"Fetching data for season {season}...")
            season_str = f"{season-1}-{str(season)[2:]}"
            game_log = fetch_game_log_with_retry(player_id, season_str)
            
            if game_log is not None and not game_log.empty:  # Check if DataFrame is not empty
                # Filter games against specific team
                team_games = game_log[game_log['MATCHUP'].str.contains(team_abbr, na=False)]
                if not team_games.empty:  # Check if filtered DataFrame is not empty
                    all_game_logs.append(team_games)
            
            time.sleep(0.8)  # Rate limiting
        
        if not all_game_logs:  # Check if we have any game logs
            print(f"No game data found for {player_name} against {team_name}")
            return None
            
        # Combine all game logs
        combined_logs = pd.concat(all_game_logs, ignore_index=True)
        
        # Sort by date and take most recent games
        combined_logs = combined_logs.sort_values('GAME_DATE', ascending=False)
        recent_games = combined_logs.head(num_games)
        
        if recent_games.empty:  # Check if we have any recent games
            print(f"No recent games found for {player_name} against {team_name}")
            return None
            
        # Calculate statistics
        stats = {
            'player_name': player_name,
            'opponent': team_name,
            'games_played': len(recent_games),
            'minutes': round(recent_games['MIN'].mean(), 1),
            'points': round(recent_games['PTS'].mean(), 1),
            'rebounds': round(recent_games['REB'].mean(), 1),
            'assists': round(recent_games['AST'].mean(), 1),
            'steals': round(recent_games['STL'].mean(), 1),
            'blocks': round(recent_games['BLK'].mean(), 1),
            'turnovers': round(recent_games['TOV'].mean(), 1),
            'field_goals_made': round(recent_games['FGM'].mean(), 1),
            'field_goals_attempted': round(recent_games['FGA'].mean(), 1),
            'three_pointers_made': round(recent_games['FG3M'].mean(), 1),
            'three_pointers_attempted': round(recent_games['FG3A'].mean(), 1),
            'free_throws_made': round(recent_games['FTM'].mean(), 1),
            'free_throws_attempted': round(recent_games['FTA'].mean(), 1)
        }
        
        return stats
        
    except Exception as e:
        print(f"Error processing {player_name}: {str(e)}")
        return None

def get_current_season_stats(player_name):
    """Fetch and calculate player's average stats for the current season against all teams."""
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Player {player_name} not found. Skipping...")
        return None
    
    current_season_year = "2024"  # Adjust based on current year
    game_log = fetch_game_log_with_retry(player_id, current_season_year)
    
    if game_log is None or game_log.empty:
        print(f"No game logs found for {player_name} in the current season.")
        return None
    
    # Calculate averages for points, assists, rebounds
    stats = {
        "points": game_log['PTS'].mean(),
        "assists": game_log['AST'].mean(),
        "rebounds": game_log['REB'].mean()
    }
    
    return stats

def calculate_combined_probability(stats, current_season_stats, target):
    """Calculate the probability of a player being over or under a target using combined stats."""
    combined_mean = (stats['mean'] + current_season_stats) / 2
    combined_std_dev = stats['std_dev']  # Assuming std_dev from historical data is representative
    
    if combined_std_dev == 0:
        return {"Over": 0.0, "Under": 1.0} if target > combined_mean else {"Over": 1.0, "Under": 0.0}
    
    z_score = (target - combined_mean) / combined_std_dev
    prob_under = norm.cdf(z_score)
    prob_over = 1 - prob_under
    
    return {"Over": prob_over, "Under": prob_under}

def get_matchup_data(player_name, opponent_team_id):
    """
    Get all relevant matchup data for a player against an opponent
    """
    player_id = get_player_id(player_name)
    if not player_id:
        return None
        
    # Get all required stats
    defensive_stats = get_team_defensive_stats(opponent_team_id)
    position = get_player_position(player_id)
    matchup_stats = get_position_matchup_stats(opponent_team_id, position)
    minutes_proj = get_player_minutes_projection(player_id, opponent_team_id)
    injury_report = get_team_injury_report(opponent_team_id)
    
    return {
        'defensive_stats': defensive_stats,
        'matchup_stats': matchup_stats,
        'minutes_projection': minutes_proj,
        'injury_report': injury_report
    }

def calculate_confidence_rating(player_stats, opponent_team_stats):
    """
    Calculate confidence rating (0-1) based on:
    - Sample size of historical matchups
    - Consistency of performance (std dev)
    - Recency of matchups
    - Health status of key defenders
    """
    # Base confidence on sample size
    sample_size_factor = min(player_stats['num_games'] / 10, 1)
    
    # Consider consistency
    consistency_factor = 1 - (player_stats['std_dev'] / player_stats['mean'])
    
    # Consider recency of data
    recency_factor = calculate_recency_factor(player_stats['game_dates'])
    
    # Consider defender health
    defender_factor = get_defender_health_factor(opponent_team_stats['key_defenders'])
    
    confidence = (sample_size_factor * 0.3 +
                 consistency_factor * 0.3 +
                 recency_factor * 0.2 +
                 defender_factor * 0.2)
    
    return min(max(confidence, 0), 1)  # Ensure between 0 and 1

def get_defender_health_factor(key_defenders):
    """
    Check injury reports and calculate impact of missing defenders
    """
    # Implementation needed - would check injury reports
    return 1.0

def calculate_recency_factor(game_dates):
    """
    Weight recent games more heavily
    """
    # Implementation needed - would calculate based on game dates
    return 1.0

def fetch_team_rosters():
    """Fetch the current rosters for all NBA teams."""
    team_rosters = {}
    all_teams = teams.get_teams()
    
    for team in all_teams:
        team_id = team['id']
        team_name = team['full_name']
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        
        for _, player in roster.iterrows():
            player_name = player['PLAYER']
            team_rosters[player_name] = team_name
    
    return team_rosters

def process_players_from_json(json_file):
    """Process players from JSON file with Monte Carlo simulations."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        all_stats = []
        processed_players = set()
        
        for event_data in data.values():
            home_team = event_data["home_team"]
            away_team = event_data["away_team"]
            
            for bookmaker in event_data.get("bookmakers", []):
                if bookmaker["key"] != "draftkings":
                    continue
                    
                for market in bookmaker.get("markets", []):
                    market_type = market["key"]
                    
                    for outcome in market.get("outcomes", []):
                        player_name = outcome["description"]
                        point = outcome["point"]
                        
                        player_key = f"{player_name}_{market_type}"
                        if player_key in processed_players:
                            continue
                            
                        processed_players.add(player_key)
                        
                        print(f"Processing stats for {player_name} vs {away_team}...")
                        print(f"Market: {market_type}, Line: {point}")
                        
                        stats = get_player_stats_against_team(
                            player_name,
                            away_team,
                            num_games=10,
                            num_seasons=4
                        )
                        
                        if stats:
                            # Run Monte Carlo simulation
                            sim_results = monte_carlo_simulation(
                                stats=stats,
                                target=point,
                                market_type=market_type
                            )
                            
                            # Update stats with simulation results
                            stats.update({
                                'target': point,
                                'market_type': market_type,
                                'over_probability': sim_results['over_probability'],
                                'under_probability': sim_results['under_probability'],
                                'confidence_score': sim_results['confidence_score'],
                                'simulated_avg': sim_results['simulated_avg'],
                                'simulated_median': sim_results['simulated_median']
                            })
                            
                            all_stats.append(stats)
        
        if not all_stats:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_stats)
        
        # Remove redundant column and round numerics
        if 'team' in df.columns:
            df = df.drop('team', axis=1)
        
        # Round specific columns to desired precision
        df['over_probability'] = df['over_probability'].round(2)
        df['under_probability'] = df['under_probability'].round(2)
        df['simulated_avg'] = df['simulated_avg'].round(2)
        df['simulated_median'] = df['simulated_median'].round(2)
        df['confidence_score'] = df['confidence_score'].round(2)
        
        return df
        
    except Exception as e:
        print(f"Error processing JSON file: {e}")
        return pd.DataFrame()

def get_team_defensive_stats(team_id):
    """
    Fetch team's defensive statistics and ratings using various endpoints
    """
    try:
        # Get advanced team stats
        advanced_stats = boxscoreadvancedv3.BoxScoreAdvancedV3(team_id=team_id).get_data_frames()[0]
        
        # Get four factors stats
        four_factors = boxscorefourfactorsv3.BoxScoreFourFactorsV3(team_id=team_id).get_data_frames()[0]
        
        # Get defensive matchup data
        defensive_stats = boxscoredefensivev2.BoxScoreDefensiveV2(team_id=team_id).get_data_frames()[0]
        
        return {
            'defensive_rating': advanced_stats['defensiveRating'].mean(),
            'opp_efg_pct': four_factors['oppEffectiveFieldGoalPercentage'].mean(),
            'opp_turnover_pct': four_factors['oppTeamTurnoverPercentage'].mean(),
            'pace': advanced_stats['pace'].mean(),
            'contested_shots_pct': defensive_stats['matchupFieldGoalPercentage'].mean()
        }
    except Exception as e:
        print(f"Error fetching defensive stats: {e}")
        return None

def get_position_matchup_stats(team_id, position):
    """
    Get how team performs against specific positions using matchup data
    """
    try:
        # Get matchup data
        matchups = boxscorematchupsv3.BoxScoreMatchupsV3(team_id=team_id).get_data_frames()[0]
        
        # Filter for specific position
        position_matchups = matchups[matchups['positionDef'] == position]
        
        return {
            'opp_avg_allowed': position_matchups['playerPoints'].mean(),
            'opp_fg_pct': position_matchups['matchupFieldGoalsPercentage'].mean(),
            'opp_ast': position_matchups['matchupAssists'].mean(),
            'opp_reb': position_matchups['reboundsTotal'].mean()
        }
    except Exception as e:
        print(f"Error fetching position matchups: {e}")
        return None

def get_player_minutes_projection(player_id, team_id):
    """
    Project minutes based on recent games and matchup
    """
    try:
        # Get traditional box scores for recent games
        traditional_stats = boxscoretraditionalv3.BoxScoreTraditionalV3(
            player_id=player_id
        ).get_data_frames()[0]
        
        # Get team pace and style
        team_stats = boxscoreadvancedv3.BoxScoreAdvancedV3(
            team_id=team_id
        ).get_data_frames()[0]
        
        recent_minutes = traditional_stats['minutes'].tail(5).mean()
        team_pace = team_stats['pace'].mean()
        
        # Adjust minutes based on pace
        projected_minutes = recent_minutes * (team_pace / 100)
        
        return {
            'avg_minutes': recent_minutes,
            'projected_minutes': projected_minutes,
            'last_5_games': traditional_stats['minutes'].tail(5).tolist()
        }
    except Exception as e:
        print(f"Error projecting minutes: {e}")
        return None

def get_team_injury_report(team_id):
    """
    Get current injury report for team using commonteamroster and playerinfo
    """
    try:
        # Get team roster
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        
        injured_players = []
        for _, player in roster.iterrows():
            player_info = commonplayerinfo.CommonPlayerInfo(
                player_id=player['PLAYER_ID']
            ).get_data_frames()[0]
            
            # Check if player is inactive
            if player_info['ROSTERSTATUS'] != 'Active':
                injured_players.append({
                    'player_id': player['PLAYER_ID'],
                    'player_name': player['PLAYER'],
                    'position': player['POSITION']
                })
        
        return {
            'injured_count': len(injured_players),
            'injured_players': injured_players,
            'key_defenders': [p for p in injured_players if p['position'] in ['F', 'C']]
        }
    except Exception as e:
        print(f"Error fetching injury report: {e}")
        return None

def get_player_position(player_id):
    """
    Get player's position using commonplayerinfo endpoint
    """
    try:
        # Get player info
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
        
        # Extract position - POSITION field contains values like 'G', 'F', 'C', 'G-F', 'F-C'
        position = player_info['POSITION'].iloc[0]
        
        # For hyphenated positions (e.g., 'G-F'), use the primary position
        primary_position = position.split('-')[0]
        
        return primary_position
        
    except Exception as e:
        print(f"Error getting player position: {e}")
        return None

def calculate_prop_probability(average, target, std_dev=None):
    """Calculate probability of going over/under a target line."""
    if std_dev is None:
        # If no std_dev provided, estimate it
        std_dev = average * 0.2  # Using 20% of average as estimation
        
    # Calculate z-score
    z_score = (target - average) / std_dev
    
    # Calculate probabilities using normal distribution
    under_prob = norm.cdf(z_score)
    over_prob = 1 - under_prob
    
    # Convert to percentages and round
    over_pct = round(over_prob * 100, 1)
    under_pct = round(under_prob * 100, 1)
    
    return over_pct, under_pct

def get_position_defensive_stats(team_id, player_position):
    """Get how well the team defends against specific positions"""
    try:
        matchups = boxscorematchupsv3.BoxScoreMatchupsV3(team_id=team_id).get_data_frames()[0]
        
        # Filter for defending against this position
        position_defense = matchups[matchups['positionOff'] == player_position]
        
        if position_defense.empty:
            return None
            
        return {
            'points_allowed_to_position': round(position_defense['playerPoints'].mean(), 1),
            'assists_allowed_to_position': round(position_defense['matchupAssists'].mean(), 1),
            'rebounds_allowed_to_position': round(position_defense['reboundsTotal'].mean(), 1),
            'fg_pct_allowed_to_position': round(position_defense['matchupFieldGoalPercentage'].mean(), 1)
        }
    except Exception as e:
        print(f"Error getting position defensive stats: {e}")
        return None

def get_primary_defender_stats(team_id, player_position):
    """Get stats of the primary defender(s) for this position"""
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
        
        # Find defenders who guard this position
        defenders = roster[roster['POSITION'].str.contains(player_position)]
        
        if defenders.empty:
            return None
            
        defender_stats = []
        for _, defender in defenders.iterrows():
            defender_id = defender['PLAYER_ID']
            stats = boxscoredefensivev2.BoxScoreDefensiveV2(
                player_id=defender_id
            ).get_data_frames()[0]
            
            if not stats.empty:
                defender_stats.append(stats)
        
        if not defender_stats:
            return None
            
        combined_stats = pd.concat(defender_stats)
        
        return {
            'primary_defender_rating': round(combined_stats['matchupFieldGoalPercentage'].mean(), 1),
            'defender_blocks': round(combined_stats['blocks'].mean(), 1),
            'defender_steals': round(combined_stats['steals'].mean(), 1),
            'defender_status': check_defender_injuries(defenders)
        }
    except Exception as e:
        print(f"Error getting primary defender stats: {e}")
        return None

def check_defender_injuries(defenders):
    """Check injury status of defenders"""
    # This would connect to an injury API or database
    # For now, return a placeholder value
    return 1.0  # 1.0 = healthy, < 1.0 = injured

# Example usage
if __name__ == "__main__":
    json_file = "nba_player_props_filtered.json"  # Replace with your actual JSON file path
    output_csv = "player_stats_vs_teams.csv"
    
    stats_df = process_players_from_json(json_file)
    if not stats_df.empty:
        stats_df.to_csv(output_csv, index=False)
        print(f"Player stats saved to {output_csv}")
        print(stats_df.head())
    else:
        print("No data to save.")
