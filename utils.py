import json
import logging
import random
from typing import Union, List

DATAFILE = "data/data.json"
# The template user data:
TEMPLATE_USER_DATA = {
    "found": [],
    "finding_id": 0,
    "emojis": "",
    "hint_given": False,
    "hints_given": 0
}

def new_response() -> dict:
    """Creates the template for a new webhook response."""
    return {
        "fulfillmentMessages": []
    }

def add_quick_replies(resp: dict, title: str, qreplies: List[str]) -> dict:
    """Adds the given quick replies to the response dictionary."""

    fulfillment_messages = resp.get("fulfillmentMessages", [])
    fulfillment_messages.append({
        "quickReplies": {
            "title": title,
            "quickReplies": qreplies
        }
    })
    resp["fulfillmentMessages"] = fulfillment_messages
    
    return resp

def add_text(resp: dict, text: str) -> dict:
    """Adds the given text to the textual response of the webhook."""
    
    for dic in resp["fulfillmentMessages"]:
        if "text" in dic:
            dic["text"]["text"].append(text)
    return resp

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

def copy_dict(*, source: dict, dest: dict, maxdepth: int = 0) -> dict:
    """Given a source dictionary, recursively copy its keys to another dict.

    The values of the destination dictionary will be of the same type as the
        corresponding values in the source dictionary, but will be empty.

    The integer maxdepth sets a limit to the recursion depth of the copy.
    A recursion depth of 0 (the minimum) only copies the current level.
    """
    
    if maxdepth < 0:
        return dest
    
    for key, value in source.items():
        if key not in dest:
            # Get the type of the value
            if (typ := type(value)) == dict:
                sub_dest = copy_dict(source=value, dest={}, maxdepth=maxdepth-1)
                dest[key] = sub_dest
            else:
                # Create the "empty" value of the correct type, e.g. [] or ""
                dest[key] = typ()

    return dest

def load_user_data(req: dict) -> dict:
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        user_id = req["originalDetectIntentRequest"]["payload"]["data"]["sender"]["id"]
    except KeyError:
        user_id = "__no_id_found__"

    user_data = data.get(user_id, {})
    # Initialize all the needed empty fields
    if not user_data:
        user_data = copy_dict(source=TEMPLATE_USER_DATA, dest=user_data)
    
    return user_data

def save_user_data(req: dict, user_data: dict) -> None:
    with open(DATAFILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        user_id = req["originalDetectIntentRequest"]["payload"]["data"]["sender"]["id"]
    except KeyError:
        user_id = "__no_id_found__"

    data[user_id] = user_data

    with open(DATAFILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def get_random_string(choices: Union[List[str], List[List[str]]]) -> str:
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