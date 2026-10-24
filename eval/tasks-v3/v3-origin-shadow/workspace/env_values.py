import re
from typing import Any


def parse(text: str) -> Any:
    if text == 'true':
        return True
    if text == 'false':
        return False
    if text == 'null':
        return None
    if re.fullmatch(r'-?[0-9]+', text):
        return int(text)
    return text


