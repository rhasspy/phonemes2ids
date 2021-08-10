import typing
from enum import Enum

STRESS: typing.Set[str] = {"ˈ", "ˌ"}

PUNCTUATION_MAP: typing.Mapping[str, str] = {";": ",", ":": ",", "?": ".", "!": "."}


class BlankBetween(str, Enum):
    TOKENS = "tokens"
    WORDS = "words"
