"""Internal causes for unverifiable checks; never serialized as verdict fields."""

from enum import Enum


class Cause(Enum):
    WORKSPACE = "workspace"
    CONTRACT = "contract"
    VERIFIER = "verifier"
    TRANSPORT = "transport"
    BUDGET = "budget"
