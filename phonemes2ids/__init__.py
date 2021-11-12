"""Tools for mapping phonemes to integer ids"""
import functools
import itertools
import logging
import operator
import typing
import unicodedata
from pathlib import Path

from phonemes2ids.const import STRESS  # pylint: disable=unused-import
from phonemes2ids.const import PUNCTUATION_MAP, BlankBetween
from phonemes2ids.utils import load_phoneme_ids  # pylint: disable=unused-import

_LOGGER = logging.getLogger("phoneme_ids")
_DIR = Path(__file__).parent

ID_LIST = typing.List[int]
WORD_ID_LIST = typing.List[ID_LIST]

__version__ = (_DIR / "VERSION").read_text().strip()

# -----------------------------------------------------------------------------


def phonemes2ids(
    word_phonemes: typing.List[typing.List[str]],
    phoneme_to_id: typing.Mapping[str, int],
    pad: typing.Optional[str] = None,
    bos: typing.Optional[str] = None,
    eos: typing.Optional[str] = None,
    blank: typing.Optional[str] = None,
    blank_word: typing.Optional[str] = None,
    blank_between: typing.Union[str, BlankBetween] = BlankBetween.WORDS,
    blank_at_start: bool = True,
    blank_at_end: bool = True,
    simple_punctuation: bool = False,
    punctuation_map: typing.Optional[typing.Mapping[str, str]] = None,
    separate: typing.Optional[typing.Collection[str]] = None,
    separate_graphemes: bool = False,
    separate_tones: bool = False,
    tone_before: bool = False,
    phoneme_map: typing.Optional[typing.Mapping[str, typing.Sequence[str]]] = None,
    missing_func: typing.Optional[
        typing.Callable[[str], typing.Optional[typing.List[int]]]
    ] = None,
    fail_on_missing: bool = False,
) -> ID_LIST:
    """
    Convert word-separated phonemes into integer ids.

    Args:
        word_phonemes: list of word phonemes, each a list of strings
        phoneme_to_id: map from phoneme to integer id
        pad: phoneme for padding vectors (currently unused)
        bos: phoneme to put at beginning of id list
        eos: phoneme to put at end of id list
        blank: phoneme to add between words or tokens
        blank_word: phoneme to add between words (when blank_between = "tokens_and_words")
        blank_between: controls where blank tokens are inserted (see const.BlankBetween)
        blank_at_start: True if blank should also be inserted before first word/token
        blank_at_end: True if blank should also be inserted after last word/token
        simple_punctuation: True if punctuation should be simplified according to punctuation_map (see const.PUNCTUATION_MAP)
        punctuation_map: map from phoneme to phoneme, used when simple_punctuation is True
        separate: collection of phonemes that should be separated out into distinct phonemes (see const.STRESS)
        separate_graphemes: True if graphemes should be decomposed into codepoints as distinct phonemes
        separate_tones: True if digits at the end of phonemes (tones) should be separated out into distinct phonemes
        tone_before: True if tones separated out are inserted before their corresponding phoneme instead of after
        phoneme_map: optional map from phoneme to phoneme sequence (used after simplification/separation)
        missing_func: function called when phoneme is missing from phoneme_to_id map (str -> [int])
        fail_on_missing: True if an error should occur when a phoneme cannot be mapped to an id

    Returns:
        ids - flat list of integer ids
    """
    if phoneme_map is None:
        phoneme_map = {}

    assert phoneme_map is not None

    if punctuation_map is None:
        punctuation_map = PUNCTUATION_MAP

    assert punctuation_map is not None

    is_separate: typing.Optional[typing.Callable[[str], bool]] = None
    if separate:
        is_separate = functools.partial(operator.contains, separate)

    blank_id: typing.Optional[int] = None
    blank_word_id: typing.Optional[int] = None
    if blank:
        blank_id = phoneme_to_id[blank]
        blank_word_id = phoneme_to_id[blank]

    if blank_word:
        # Separate phoneme between words
        blank_word_id = phoneme_to_id[blank_word]

    # Transform into phoneme ids
    word_phoneme_ids: WORD_ID_LIST = []

    def maybe_extend_ids(
        phoneme: str,
        target: typing.Union[ID_LIST, WORD_ID_LIST],
        append_list: bool = True,
    ):
        if not phoneme:
            return

        maybe_id = phoneme_to_id.get(phoneme)
        if maybe_id is not None:
            if append_list:
                typing.cast(WORD_ID_LIST, target).append([maybe_id])
            else:
                typing.cast(ID_LIST, target).append(maybe_id)
            return

        if missing_func is not None:
            maybe_ids = missing_func(phoneme)
            if maybe_ids:
                if append_list:
                    typing.cast(WORD_ID_LIST, target).append(maybe_ids)
                else:
                    typing.cast(ID_LIST, target).extend(maybe_ids)
                return

        if fail_on_missing:
            raise ValueError(f"No id for phoneme: {phoneme}")

    # Add beginning-of-sentence symbol
    if bos:
        maybe_extend_ids(bos, word_phoneme_ids)

    if (blank_id is not None) and blank_at_start:
        # Blank token at start
        word_phoneme_ids.append([blank_id])

    last_word_idx = len(word_phonemes) - 1
    for word_idx, word in enumerate(word_phonemes):
        word_ids: typing.List[int] = []

        if separate_graphemes:
            word = list(
                itertools.chain.from_iterable(
                    unicodedata.normalize("NFD", p) for p in word
                )
            )

        for phoneme in word:
            tone = ""

            if separate_tones:
                # Separate tones (digits at the end of a phoneme)
                tone_chars = []

                # Strip digits off the back of the phoneme (reversed)
                while phoneme and phoneme[-1].isdigit():
                    tone_chars.append(phoneme[-1])
                    phoneme = phoneme[:-1]

                if tone_chars:
                    tone = "".join(reversed(tone_chars))

                if tone and tone_before:
                    # Insert tone before corresponding phoneme
                    maybe_extend_ids(tone, word_ids, append_list=False)

            if is_separate is None:
                # No more splitting
                sub_phonemes = [phoneme]
            else:
                # Separate out stress, etc.
                assert separate is not None
                sub_phonemes = []

                before_split = ""
                for codepoint in phoneme:
                    if codepoint in separate:
                        # Split here
                        if before_split:
                            sub_phonemes.append(before_split)
                            before_split = ""

                        sub_phonemes.append(codepoint)
                    else:
                        before_split += codepoint

                if before_split:
                    sub_phonemes.append(before_split)

            for sub_phoneme in sub_phonemes:
                if not sub_phoneme:
                    continue

                if simple_punctuation and punctuation_map:
                    sub_phoneme = punctuation_map.get(sub_phoneme, sub_phoneme)

                to_phonemes = phoneme_map.get(sub_phoneme)
                if to_phonemes:
                    # Mapped to one or more phonemes
                    for to_phoneme in to_phonemes:
                        maybe_extend_ids(to_phoneme, word_ids, append_list=False)
                else:
                    # No map
                    maybe_extend_ids(sub_phoneme, word_ids, append_list=False)

            if tone and (not tone_before):
                # Insert tone after corresponding phoneme
                maybe_extend_ids(tone, word_ids, append_list=False)

        if word_ids:
            if (blank_word_id is not None) and (
                blank_between in {BlankBetween.WORDS, BlankBetween.TOKENS_AND_WORDS}
            ):
                # Blank phoneme between each word (list of tokens)
                if (word_idx != last_word_idx) or blank_at_end:
                    word_ids.append(blank_word_id)

            if (blank_id is not None) and (
                blank_between in {BlankBetween.TOKENS, BlankBetween.TOKENS_AND_WORDS}
            ):
                # Blank phoneme between each token
                num_blanks = len(word_ids)
                word_phoneme_ids.append(
                    list(
                        # [p, blank, p, blank, ...]
                        itertools.chain.from_iterable(
                            # ((p, blank), (p, blank), ...)
                            itertools.zip_longest(
                                word_ids, itertools.repeat(blank_id, num_blanks)
                            )
                        )
                    )
                )

                if (
                    (word_idx == last_word_idx)
                    and (not blank_at_end)
                    and word_phoneme_ids[-1]
                ):
                    # Drop last blank
                    word_phoneme_ids[-1].pop()
            else:
                # No blanks between tokens
                word_phoneme_ids.append(word_ids)

    # Add end-of-sentence symbol
    if eos:
        maybe_extend_ids(eos, word_phoneme_ids)

    return list(itertools.chain.from_iterable(word_phoneme_ids))


# -----------------------------------------------------------------------------


def learn_phoneme_ids(
    word_phonemes: typing.List[typing.List[str]],
    all_phonemes: typing.Set[str],
    all_phoneme_counts: typing.Optional[typing.Counter[str]] = None,
    simple_punctuation: bool = False,
    punctuation_map: typing.Optional[typing.Mapping[str, str]] = None,
    separate: typing.Optional[typing.Collection[str]] = None,
    separate_graphemes: bool = False,
    separate_tones: bool = False,
    phoneme_map: typing.Optional[typing.Mapping[str, str]] = None,
):
    """
    Discover phonemes from examples.

    Args:
        word_phonemes: list of word phonemes, each a list of strings
        all_phonemes: set of distinct phonemes found (modified by function)
        all_phoneme_counts: optional Counter with observed phoneme counts (modified by function)
        simple_punctuation: True if punctuation should be simplified according to punctuation_map (see const.PUNCTUATION_MAP)
        punctuation_map: map from phoneme to phoneme, used when simple_punctuation is True
        separate: collection of phonemes that should be separated out into distinct phonemes (see const.STRESS)
        separate_graphemes: True if graphemes should be decomposed into codepoints as distinct phonemes
        separate_tones: True if digits at the end of phonemes (tones) should be separated out into distinct phonemes
        phoneme_map: optional map from phoneme to phoneme sequence (used after simplification/separation)

    Returns:
        None - all_phonemes and all_phoneme_counts are modified
    """
    if phoneme_map is None:
        phoneme_map = {}

    if punctuation_map is None:
        punctuation_map = PUNCTUATION_MAP

    is_separate: typing.Optional[typing.Callable[[str], bool]] = None
    if separate:
        is_separate = functools.partial(operator.contains, separate)

    for word in word_phonemes:
        if separate_graphemes:
            word = list(
                itertools.chain.from_iterable(
                    unicodedata.normalize("NFD", p) for p in word
                )
            )

        for phoneme in word:
            if separate_tones:
                # Separate tones (digits at the end of a phoneme)
                tone_chars = []

                # Strip digits off the back of the phoneme (reversed)
                while phoneme and phoneme[-1].isdigit():
                    tone_chars.append(phoneme[-1])
                    phoneme = phoneme[:-1]

                if tone_chars:
                    tone = "".join(reversed(tone_chars))
                    all_phonemes.add(tone)
                    if all_phoneme_counts is not None:
                        all_phoneme_counts[tone] += 1

            if is_separate is None:
                # No more splitting
                sub_phonemes = [phoneme]
            else:
                # Separate out stress, etc.
                assert separate is not None
                sub_phonemes = []

                before_split = ""
                for codepoint in phoneme:
                    if is_separate(codepoint):
                        # Split here
                        if before_split:
                            sub_phonemes.append(before_split)
                            before_split = ""

                        sub_phonemes.append(codepoint)
                    else:
                        before_split += codepoint

                if before_split:
                    sub_phonemes.append(before_split)

            for sub_phoneme in sub_phonemes:
                if not sub_phoneme:
                    continue

                if simple_punctuation:
                    sub_phoneme = punctuation_map.get(sub_phoneme, sub_phoneme)

                to_phonemes = phoneme_map.get(sub_phoneme)
                if to_phonemes:
                    # Mapped to one or more phonemes
                    for to_phoneme in to_phonemes:
                        all_phonemes.add(to_phoneme)

                        if all_phoneme_counts is not None:
                            all_phoneme_counts[to_phoneme] += 1
                else:
                    # No map
                    all_phonemes.add(sub_phoneme)

                    if all_phoneme_counts is not None:
                        all_phoneme_counts[sub_phoneme] += 1
