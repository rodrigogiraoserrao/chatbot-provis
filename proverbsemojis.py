import flask
from flask import request
import json
import logging
import random

from proverbs import proverbs

DATAFILE = "data/data.json"

# Replies for when the user gets the correct proverb.
CORRECT = [
    "Certo!",
    "Certíssimo!",
    "Correto!",
    "Acertaste!",
    "É isso mesmo!",
    "Mesmo na mouche!"
]

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

def get_random_string(choices):
    """Build a random reply from the given set of option strings.

    `choices` might be a list of strings, in which case a random choice
        is returned, or
    `choices` might be a list of lists of strings, in which case a concatenation
        of random choices from each sub-list is returned.
    Examples:
        ["a", "b", "c"] -> "a"
        [["a", "A"], ["b"], ["c", "C"]] -> "abC"
    """

    if not choices:
        return ""

    if type(choices[0]) == str:
        return random.choice(choices)
    else:
        return "".join(random.choice(subl for subl in choices))

def make_reply(req, text):
    """Helper function to set the reply text."""

    req["fulfillmentText"] = text
    return req

def main_give_up(req):
    """Called when the user wants to give up on a given proverb."""
    # (TODO)
    return req

def main_hint(req):
    """Called when the user asks for a hint on a given proverb."""
    # (TODO)
    return req

def main_progress(req):
    """Called when the user asks for its progress."""
    # (TODO)
    return req

def main_make_suggestion(req):
    """Called when the user wants to make a new suggestion."""
    # (TODO)
    return req

def main_play(req):
    """Called when the user wants to play."""

    user_data = load_user_data(req)
    found = set(user_data.setdefault("found", []))
    finding_id = user_data.setdefault("finding_id", None)

    if finding_id:
        emojis = user_data["emojis"]
        return make_reply(req, emojis + "\nSe estiver a ficar difícil podes desistir ou pedir uma pista!")

    existing_ids = {proverb["id"] for proverb in proverbs}
    to_be_found = list(existing_ids - found)

    if not to_be_found:
        return make_reply(req, "Já descobriste todos os provérbios!")

    proverb_id = random.choice(to_be_found)
    for proverb in proverbs:
        if proverb["id"] == proverb_id:
            break

    req = make_reply(req, proverb["emojis"])
    user_data["emojis"] = proverb["emojis"]
    user_data["finding_id"] = proverb_id

    save_user_data(req, user_data)

    return req

def check_proverb(req):
    """Check if the proverb the user said is correct or not."""

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
            user_data["emojis"] = ""
            save_user_data(req, user_data)
            return make_reply(req, get_random_string(CORRECT))

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

    # Map some intents to some handlers
    intent_mapping = {
        "main_play": main_play,
        "main_give_up": main_give_up,
        "main_hint": main_hint,
        "main_progress": main_progress,
        "main_make_suggestion": main_make_suggestion
    }

    if intent_name in intent_mapping:
        func = intent_mapping[intent_name]
        req_json = func(req_json)
    elif intent_name.startswith("proverb_"):
        req_json = check_proverb(req_json)

    return flask.jsonify(req_json)