# NBA Player Prop Odds and Analysis

This repository contains a set of Python scripts designed to fetch, filter, and analyze NBA player prop odds and statistics. The scripts utilize The Odds API to gather bookmaker odds and the NBA API to retrieve player and team statistics. The analysis includes advanced statistical methods such as Monte Carlo simulations to predict player performance.

## Features

- **Fetch NBA Player Odds**: Retrieve today's NBA player prop odds from The Odds API.
- **Filter Bookmaker Data**: Process and filter odds data to focus on specific bookmakers like DraftKings.
- **Statistical Analysis**: Use Monte Carlo simulations to estimate probabilities of player performance metrics.
- **NBA API Integration**: Fetch player and team statistics from the NBA API for in-depth analysis.

## Scripts Overview

### `fetch_tonight_player_odds.py`

- **Purpose**: Fetches today's NBA event IDs and player prop odds from The Odds API.
- **API Used**: The Odds API (https://api.the-odds-api.com)
- **Key Functionality**:
  - Retrieves event IDs for today's NBA games.
  - Fetches player prop odds for points, rebounds, and assists.
  - Saves the data to a JSON file for further processing.

### `remove_key.py`

- **Purpose**: Filters the JSON data to retain only specific bookmakers.
- **Functionality**:
  - Loads player prop odds from a JSON file.
  - Filters the data to keep only odds from DraftKings.
  - Saves the filtered data to a new JSON file.

### `average_stats_today_players.py`

- **Purpose**: Performs advanced statistical analysis on player performance.
- **Key Features**:
  - Monte Carlo simulations to predict player performance probabilities.
  - Fetches historical player stats against specific teams.
  - Integrates with the NBA API to retrieve player and team statistics.
  - Calculates confidence scores and probabilities for player performance metrics.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/freshened/nba-prop-analytics.git
   cd nba-player-prop-odds
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - Replace the placeholder API key in `fetch_tonight_player_odds.py` with your actual API key from The Odds API.

## Usage

1. **Fetch Odds**: Run `fetch_tonight_player_odds.py` to fetch and save today's player prop odds.
   ```bash
   python fetch_tonight_player_odds.py
   ```

2. **Filter Bookmakers**: Run `remove_key.py` to filter the odds data for specific bookmakers.
   ```bash
   python remove_key.py
   ```

3. **Analyze Player Stats**: Run `average_stats_today_players.py` to perform statistical analysis on player performance.
   ```bash
   python average_stats_today_players.py
   ```

4. **View Output**: Check the `nba_player_props_filtered.json` file for the filtered odds data and analysis results.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for any bugs or feature requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [The Odds API](https://the-odds-api.com) for providing sports betting data.
- [NBA API](https://github.com/swar/nba_api) for providing access to NBA statistics.
