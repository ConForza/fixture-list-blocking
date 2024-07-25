# Imports
import os

import requests
import json
import datetime as dt
from dateutil import parser

# Global authentication details. Sensitive information stored as env variables
FOOTBALL_URI = "https://api.football-data.org/v4/teams/62/matches"
FOOTBALL_KEY = os.environ.get("FOOTBALL_KEY")
API_URL = "https://acuityscheduling.com/api/v1/"
USER_NAME = os.environ.get("USER_NAME")
ACUITY_KEY = os.environ.get("ACUITY_KEY")
# Headers for Acuity
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json"
}

# Load block IDs from past-created blocks
with open("ids.json", mode="r") as file:
    block_ids = json.load(file)


# Load all Everton home game details
def get_fixtures():
    # Football-data authentication
    headers = {
        'X-Auth-Token': FOOTBALL_KEY
    }

    # Query parameters to get home fixtures only
    params = {
        "status": "SCHEDULED",
        "venue": "HOME"
    }

    response = requests.get(url=FOOTBALL_URI, headers=headers, params=params)
    # Load result in JSON format
    data = response.json()

    # Create new array of dictionaries to better, more concisely organise data
    fixture_list = []

    for match in data["matches"]:
        fixture_list.append(
            {
                "id": match["id"],
                "opponent": match["awayTeam"]["tla"],
                "date": match["utcDate"],
                "updated": match["lastUpdated"]
            }
        )

    # Return created array
    return fixture_list


# Update blocks on Acuity. There is no PUT method for this in the documentation
def update_block(match):
    # Get Acuity block ID from ids.json, matching it with the current fixture ID
    block_id = block_ids[str(match["id"])]
    # Delete existing block from the schedule
    response = requests.delete(
        url=API_URL + "blocks/" + str(block_id),
        auth=(USER_NAME, ACUITY_KEY),
        headers=HEADERS
    )

    # If delete was successful, recreate block with the updated details, else throw error
    if response.status_code < 300:
        create_block(match)
    else:
        print("There has been an error trying to update match " + str(match["id"]))


# Create block from fixture details
def create_block(match):
    # Make the start time of block 1hr30min from kick off time, to give me a chance to get to the stadium
    start_time = dt.datetime.isoformat(dt.datetime.fromisoformat(match["date"]) - dt.timedelta(hours=1, minutes=30))
    # Add 4 hours from kick off time to prevent people booking in after kick off
    end_time = dt.datetime.isoformat(dt.datetime.fromisoformat(match["date"]) + dt.timedelta(hours=4))
    # Create a note on the appointment calendar with the specific fixture details
    notes = "Everton v " + match["opponent"]

    # Initialize data
    data = {
        "start": start_time,
        "end": end_time,
        "calendarID": "1802799",
        "notes": notes
    }

    # Post data
    response = requests.post(
        url=API_URL + "blocks",
        auth=(USER_NAME, ACUITY_KEY),
        headers=HEADERS,
        json=data
    )

    # Add returned block ID from Acuity to IDs file. This will allow updates to this later
    block_id = str(response.json()["id"])
    block_ids[match["id"]] = block_id
    with open("ids.json", mode="w") as f:
        json.dump(block_ids, f)


# Iterate through get_fixtures(), checking current blocks to see if block already exists
# If the block exists check to see if fixture was updated over the past day. If so, update block
# If it doesn't exist, create block

for fixture in get_fixtures():
    if str(fixture["id"]) in block_ids:
        current_time = dt.datetime.now(dt.timezone.utc)
        if parser.parse(fixture["updated"]) >= current_time - dt.timedelta(days=1):
            update_block(fixture)
    else:
        create_block(fixture)



