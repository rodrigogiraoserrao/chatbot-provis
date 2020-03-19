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

def make_reply(req, text):
    req["fulfillmentText"] = text

    return req

def main_play(req):
    user_data = load_user_data(req)
    found = set(user_data.setdefault("found", []))
    finding_id = user_data.setdefault("finding_id", None)

    if finding_id:
        emojies = user_data["emojies"]
        return make_reply(req, emojies + "\nSe estiver a ficar difícil podes desistir ou pedir uma pista!")

    existing_ids = {proverb["id"] for proverb in proverbs}
    to_be_found = list(existing_ids - found)

    if not to_be_found:
        return make_reply(req, "Já descobriste todos os provérbios!")

    proverb_id = random.choice(to_be_found)
    for proverb in proverbs:
        if proverb["id"] == proverb_id:
            break

    req = make_reply(req, proverb["emojies"])
    user_data["emojies"] = proverb["emojies"]
    user_data["finding_id"] = proverb_id

    save_user_data(req, user_data)

    return req


def check_proverb(req):
    user_data = load_user_data(req)
    finding_id = user_data.setdefault("finding_id", None)

    if not finding_id:
        return make_reply(req, "Para tentares adivinhar um provérbio, escreve 'jogar'!")

    intent_name = req["queryResult"]["intent"]["displayName"]

    # Look for the proverb with the ID of the proverb the user is trying
    ## to guess and check if the intents match
    for proverb in proverbs:
        if finding_id == proverb["id"] and intent_name == proverb["intent"]:
            found = user_data.setdefault("found", [])
            found.append(finding_id)
            user_data["found"] = found
            user_data["finding_id"] = None
            save_user_data(req, user_data)
            return make_reply(req, "Certíssimo!")

        elif finding_id == proverb["id"]:
            return make_reply(req, "Woops, erraste...")


logger = create_logger("proverbs", "proverbios.log")
def webhook():
    """Entry point from the main flask server."""

    req_json = request.json

    # Log the request
    logger.debug(json.dumps(req_json, indent=4, sort_keys=True))

    # Fetch the intent name
    intent_name = req_json["queryResult"]["intent"]["displayName"]
    logger.debug(f"Got intent '{intent_name}'")

    if intent_name == "main_play":
        req_json = main_play(req_json)

    elif intent_name.startswith("proverb_"):
        req_json = check_proverb(req_json)

    return flask.jsonify(req_json)