import requests
import json
from datetime import datetime

API_KEY = "585cf61ec047faab3d59b6daa8df7cdd"  # Replace with your actual API key
SPORT = "basketball_nba"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

def get_todays_event_ids():
    """Fetch today's NBA event IDs."""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/{SPORT}/events"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h",  # Only needs to fetch events, market type here is arbitrary
        "dateFormat": "iso",
        "oddsFormat": "decimal"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}, {response.json()}")

    events = response.json()
    return [event["id"] for event in events]

def get_all_player_props(event_id):
    """Fetch all player props for a given event ID."""
    url = f"{BASE_URL}/{SPORT}/events/{event_id}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "player_points,player_rebounds,player_assists",  # Add more markets as needed
        "oddsFormat": "decimal"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching player props for event {event_id}: {response.status_code}")
        return None

    return response.json()

def main():
    """Main function to fetch all player props for today's games."""
    try:
        event_ids = get_todays_event_ids()
        print(f"Fetched {len(event_ids)} events for today.")

        all_props = {}
        for event_id in event_ids:
            print(f"Fetching player props for event: {event_id}")
            event_props = get_all_player_props(event_id)
            if event_props:
                all_props[event_id] = event_props

        # Save the props to a JSON file
        with open("nba_player_props.json", "w") as f:
            json.dump(all_props, f, indent=4)

        print("Player props saved to nba_player_props.json")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
