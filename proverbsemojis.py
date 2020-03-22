import flask
from flask import request
import json
import random

from proverbs import proverbs
from utils import load_user_data, save_user_data, get_random_string, \
                    create_logger, new_response, add_quick_replies, add_text

# Quick replies
QR_PLAY = "Jogar 🎮"
QR_PLAY_AGAIN = "Jogar outro 🎮"
QR_GIVE_UP = "Desistir 😢"
QR_HINT = "Pista 🔎"
QR_PROGRESS = "Progresso 🥉🥈🥇"
QR_SUGGESTION = "Sugerir provérbio 👨‍🎓"
QR_GOODBYE = "Adeus! 👋"

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

def main_give_up(req):
    """Called when the user wants to give up on a given proverb."""

    resp = new_response()
    user_data = load_user_data(req)
    # If the user isn't trying to guess any proverb, the user can't give up
    if not user_data["finding_id"]:
        return add_text(resp, "Se não estás a tentar adivinhar nenhum provérbio, queres _\"desistir\"_ de quê?")
    # If the user has found all other proverbs, don't let the user give up
    if len(user_data["found"]) == len(proverbs) - 1:
        return add_text(resp, "Só te falta mais este provérbio! Não podes desistir agora \U0001F4AA")

    # Otherwise, stop signaling this proverb as the one being guessed
    user_data["finding_id"] = 0
    user_data["emojis"] = ""
    save_user_data(req, user_data)

    reply = get_random_string(GIVE_UP)
    return add_text(resp, reply)

def main_hint(req):
    """Called when the user asks for a hint on a given proverb."""
    # (TODO)
    return new_response()

def main_progress(req):
    """Called when the user asks for its progress."""
    # (TODO)
    return new_response()

def main_make_suggestion(req):
    """Called when the user wants to make a new suggestion."""
    # (TODO)
    return new_response()

def main_play(req):
    """Called when the user wants to play."""

    resp = new_response()
    user_data = load_user_data(req)
    found = set(user_data.setdefault("found", []))
    finding_id = user_data.setdefault("finding_id", 0)

    if finding_id:
        emojis = user_data["emojis"]
        resp = add_text(resp, emojis)
        return add_quick_replies(
            resp,
            "Se estiver a ficar difícil podes desistir ou pedir uma pista!",
            [
                QR_HINT,
                QR_GIVE_UP,
                QR_PROGRESS,
                QR_SUGGESTION,
                QR_GOODBYE
            ]
        )

    existing_ids = {*proverbs.keys()}
    to_be_found = list(existing_ids - found)

    if not to_be_found:
        return add_quick_replies(
            resp,
            "Já descobriste todos os provérbios!",
            [
                QR_SUGGESTION,
                QR_GOODBYE
            ]
        )

    proverb_id = random.choice(to_be_found)
    proverb = proverbs[proverb_id]

    resp = add_quick_replies(
        resp,
        proverb["emojis"],
        [
            QR_GIVE_UP,
            QR_PROGRESS,
            QR_SUGGESTION,
            QR_GOODBYE
        ]
    )
    user_data["emojis"] = proverb["emojis"]
    user_data["finding_id"] = proverb_id

    save_user_data(req, user_data)

    return resp

def check_proverb(req):
    """Check if the proverb the user said is correct or not."""

    resp = new_response()
    user_data = load_user_data(req)
    finding_id = user_data.setdefault("finding_id", 0)

    if not finding_id:
        resp = add_text(resp, "Para tentares adivinhar um provérbio, escreve 'jogar'!")
        return add_quick_replies(resp,
                                "Ou escolhe qualquer uma das outras opções...",
                                [
                                    QR_PLAY,
                                    QR_PROGRESS,
                                    QR_SUGGESTION,
                                    QR_GOODBYE
                                ])

    intent_name = req["queryResult"]["intent"]["displayName"]

    # Get the proverb the player is trying to guess and check for correct guess
    proverb = proverbs[finding_id]
    # If the intents match, the player got it right!
    if intent_name == proverb["intent"]:
        found = user_data.setdefault("found", [])
        found.append(finding_id)
        user_data["found"] = found
        user_data["finding_id"] = None
        user_data["emojis"] = ""
        save_user_data(req, user_data)

        resp = add_text(resp, get_random_string(CORRECT))
        return add_quick_replies(resp,
                                "E agora?",
                                [
                                    QR_PLAY_AGAIN,
                                    QR_PROGRESS,
                                    QR_SUGGESTION,
                                    QR_GOODBYE
                                ])

    else:
        resp = add_text(resp, "Woops, erraste...")
        return add_quick_replies(resp,
                                "Tenta outra vez!",
                                [
                                    QR_HINT,
                                    QR_GIVE_UP,
                                    QR_PROGRESS,
                                    QR_SUGGESTION,
                                    QR_GOODBYE
                                ])

def test(req: dict):
    pre = new_response()
    return add_quick_replies(pre, "teste", ["uma", "duas", "três"])

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
    elif intent_name == "teste":
        req_json = test(req_json)

    return flask.jsonify(req_json)