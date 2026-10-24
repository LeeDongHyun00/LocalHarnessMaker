from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping

@dataclass
class Setting:
    value: Any
    source: str


from env_values import parse as _parse


def resolve(defaults: Mapping[str, Any], file_values: Mapping[str, Any],
            environment: Mapping[str, str], prefix: str = 'APP_') -> dict[str, Setting]:
    env = {key[len(prefix):].lower(): value for key, value in environment.items()
           if key.startswith(prefix) and key[len(prefix):]}
    result: dict[str, Setting] = {}
    for key in dict.fromkeys([*defaults, *file_values, *env]):
        if key in env:
            value, source = _parse(env[key]), 'environment'
        elif file_values.get(key):
            value, source = file_values[key], 'file'
        else:
            value, source = defaults[key], 'default'
        result[key] = Setting(deepcopy(value), source)
    return result
