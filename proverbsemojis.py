import flask
from flask import request
import json
import random

from proverbs import proverbs
from utils import load_user_data, save_user_data, get_random_string, create_logger

# Replies for when the user gets the correct proverb.
CORRECT = [
    "Certo!",
    "Certíssimo!",
    "Correto!",
    "Acertaste!",
    "É isso mesmo!",
    "Mesmo na mouche!"
]

GIVE_UP = [
    "É uma pena desistires..."
]

def make_reply(req, text):
    """Helper function to set the reply text."""

    req["fulfillmentText"] = text
    return req

def main_give_up(req):
    """Called when the user wants to give up on a given proverb."""

    user_data = load_user_data(req)
    # If the user isn't trying to guess any proverb, the user can't give up
    if not user_data["finding_id"]:
        return make_reply(req, "Se não estás a tentar adivinhar nenhum provérbio, queres _\"desistir\"_ de quê?")
    # If the user has found all other proverbs, don't let the user give up
    if len(user_data["found"]) == len(proverbs) - 1:
        return make_reply(req, "Só te falta mais este provérbio! Não podes desistir agora \U0001F4AA")

    # Otherwise, stop signaling this proverb as the one being guessed
    user_data["finding_id"] = 0
    user_data["emojis"] = ""
    save_user_data(req, user_data)

    reply = get_random_string(GIVE_UP)
    return make_reply(req, reply)

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
    finding_id = user_data.setdefault("finding_id", 0)

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
    logger.debug(json.dumps(req_json))

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