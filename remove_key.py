import json

# Load the JSON data from the file
with open('nba_player_props.json', 'r') as file:
    data = json.load(file)

# Iterate through each event
for event_id, event_data in data.items():
    # Filter the bookmakers to keep only 'draftkings' and 'fanduel'
    event_data['bookmakers'] = [
        bookmaker for bookmaker in event_data['bookmakers']
        if bookmaker['key'] in ['draftkings']
    ]

# Save the filtered data back to the JSON file
with open('nba_player_props_filtered.json', 'w') as file:
    json.dump(data, file, indent=4)