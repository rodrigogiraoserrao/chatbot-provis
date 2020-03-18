import flask
from flask import request
import json

from proverbs import proverbs

DATAFILE = "data.json"

def load_user_data(req):
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        user_id = req["originalDetectIntentRequest"]["payload"]["data"]["sender"]["id"]
    except KeyError:
        user_id = "__no_id_found__"


    return data.get(user_id, {})

def main_play(req):
    user_data = load_user_data(req)
    found = set(user_data.get("found", []))

    existing = set(*range(len(proverbs)))
    to_be_found = existing - found

    if not to_be_found:
        req["queryResult"]["fulfillmentText"] = "Encontraste todos, já!"

def webhook(logger):
    """Entry point from the main flask server."""

    req_json = request.json

    # Log the request
    logger.debug(json.dumps(req_json))

    return flask.jsonify(req_json)