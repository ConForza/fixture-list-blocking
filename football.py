import os

import requests
import json
import datetime as dt
from dateutil import parser

FOOTBALL_URI = "https://api.football-data.org/v4/teams/62/matches"
FOOTBALL_KEY = os.environ.get("FOOTBALL_KEY")
API_URL = "https://acuityscheduling.com/api/v1/"
USER_NAME = os.environ.get("USER_NAME")
ACUITY_KEY = os.environ.get("ACUITY_KEY")
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json"
}

with open("ids.json", mode="r") as file:
    block_ids = json.load(file)


def get_fixtures():
    headers = {
        'X-Auth-Token': FOOTBALL_KEY
    }

    params = {
        "status": "SCHEDULED",
        "venue": "HOME"
    }

    response = requests.get(url=FOOTBALL_URI, headers=headers, params=params)
    data = response.json()

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

    return fixture_list


def update_block(match):
    block_id = block_ids[str(match["id"])]
    response = requests.delete(
        url=API_URL + "blocks/" + str(block_id),
        auth=(USER_NAME, ACUITY_KEY),
        headers=HEADERS
    )

    if response.status_code < 300:
        create_block(match)
    else:
        print("There has been an error trying to update match " + str(match["id"]))


def create_block(match):
    start_time = dt.datetime.isoformat(dt.datetime.fromisoformat(match["date"]) - dt.timedelta(hours=1, minutes=30))
    end_time = dt.datetime.isoformat(dt.datetime.fromisoformat(match["date"]) + dt.timedelta(hours=4))
    notes = "Everton v " + match["opponent"]

    data = {
        "start": start_time,
        "end": end_time,
        "calendarID": "1802799",
        "notes": notes
    }

    response = requests.post(
        url=API_URL + "blocks",
        auth=(USER_NAME, ACUITY_KEY),
        headers=HEADERS,
        json=data
    )

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



