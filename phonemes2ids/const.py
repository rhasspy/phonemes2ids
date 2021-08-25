"""Constants and enums"""
import typing
from enum import Enum

STRESS: typing.Set[str] = {"ˈ", "ˌ"}
"""Default stress characters"""

PUNCTUATION_MAP: typing.Mapping[str, str] = {";": ",", ":": ",", "?": ".", "!": "."}
"""Default punctuation simplification into short (,) and long (.) pauses"""


class BlankBetween(str, Enum):
    """Placement of blank tokens"""

    TOKENS = "tokens"
    """Blank between every token/phoneme"""

    WORDS = "words"
    """Blank between every word"""
