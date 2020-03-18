import flask
from flask import request
import json
import logging
import random

from proverbs import proverbs

DATAFILE = "data.json"

def create_logger(name: str, filename: str) -> logging.Logger:
    """Create a logger with name ``name`` that logs to the file ``filename``.

    The logger returned is set to DEBUG level.
    This is based off of the logging cookbook available at
    https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.FileHandler(filename, encoding = "utf-8")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)
    return logger

def load_user_data(req):
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        user_id = req["originalDetectIntentRequest"]["payload"]["data"]["sender"]["id"]
    except KeyError:
        user_id = "__no_id_found__"

    return data.get(user_id, {})

def save_user_data(req, user_data):
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        user_id = req["originalDetectIntentRequest"]["payload"]["data"]["sender"]["id"]
    except KeyError:
        user_id = "__no_id_found__"

    data[user_id] = user_data

    with open(DATAFILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def main_play(req):
    user_data = load_user_data(req)
    found = set(user_data.get("found", []))

    existing = set(range(len(proverbs)))
    to_be_found = list(existing - found)

    if not to_be_found:
        req["fulfillmentText"] = "Já descobriste todos os provérbios!"
        return req

    proverb_index = random.choice(to_be_found)
    proverb = proverbs[proverb_index][0]
    req["fulfillmentText"] = proverb
    user_data["finding"] = proverb_index

    save_user_data(req, user_data)

    return req


logger = create_logger("proverbs", "proverbios.log")
def webhook():
    """Entry point from the main flask server."""

    req_json = request.json

    # Log the request
    logger.debug(json.dumps(req_json))

    # Fetch the intent name
    intent_name = req_json["queryResult"]["intent"]["displayName"]
    logger.debug(f"Got intent '{intent_name}'")

    if intent_name == "main_play":
        req_json = main_play(req_json)

    return flask.jsonify(req_json)