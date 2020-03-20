#! /usr/bin/python3

import os
import re
import sys
import unicodedata

CONVERSION_TEMPLATE = """{{
    "id": {prov_id},
    "emojis": "{conv}", # {names}
    "intent": None
}},\n"""

escape_sequence_re = re.compile(r".*(\\[uU][0-9a-fA-F]+)")

def escape(char):
    """Takes a character and returns its \\U escaped string and the char name."""

    escaped_str = str(char.encode("unicode_escape"))
    if match := escape_sequence_re.match(escaped_str):
        return match.group(1), unicodedata.name(char)
    else:
        raise ValueError(f"Could not escape {char}")


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Call this program with a file to convert.")
        sys.exit()

    try:
        with open(filename, "r", encoding="utf8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File {filename} not found!")

    # List of pairs (conversion, list of emojie names)
    converted_lines = []
    for line in lines:
        new_line = ""
        names = []
        for char in line:
            if ord(char) < 4096:
                new_line += char
            else:
                escaped, name = escape(char)
                names.append(f"({name})")
                new_line += escaped

        new_line = new_line.strip()

        converted_lines.append((new_line, names))

    file_name, file_ext = os.path.splitext(filename)
    file_name = file_name + "_conv" + file_ext
    
    with open(file_name, "w", encoding="utf8") as f:
        for line, (conv, names) in enumerate(converted_lines):
            if conv:
                f.write(CONVERSION_TEMPLATE.format(
                    prov_id = line + 1,
                    conv = conv,
                    names = " ".join(names)
                ))