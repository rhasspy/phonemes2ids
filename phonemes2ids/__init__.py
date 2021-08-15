import functools
import itertools
import logging
import operator
import typing
import unicodedata

from .const import PUNCTUATION_MAP, BlankBetween, STRESS
from .utils import partition, load_phoneme_ids, load_phoneme_map

_LOGGER = logging.getLogger("phoneme_ids")

# -----------------------------------------------------------------------------


def phonemes2ids(
    word_phonemes: typing.List[typing.List[str]],
    phoneme_to_id: typing.Mapping[str, int],
    pad: typing.Optional[str] = None,
    bos: typing.Optional[str] = None,
    eos: typing.Optional[str] = None,
    blank: typing.Optional[str] = None,
    blank_between: typing.Union[str, BlankBetween] = BlankBetween.WORDS,
    simple_punctuation: bool = False,
    punctuation_map: typing.Optional[typing.Mapping[str, str]] = None,
    separate: typing.Optional[typing.Collection[str]] = None,
    separate_graphemes: bool = False,
    separate_tones: bool = False,
    phoneme_map: typing.Optional[typing.Mapping[str, str]] = None,
    missing_func: typing.Optional[
        typing.Callable[[str], typing.Optional[typing.List[int]]]
    ] = None,
) -> typing.List[int]:
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
    if blank:
        blank_id = phoneme_to_id[blank]

    # Transform into phoneme ids
    word_phoneme_ids = []

    def maybe_extend_ids(
        phoneme: str, target: typing.List[int], append_list: bool = True
    ):
        if not phoneme:
            return

        maybe_id = phoneme_to_id.get(phoneme)
        if maybe_id is not None:
            if append_list:
                maybe_id = [maybe_id]
            target.append(maybe_id)
            return

        if missing_func is not None:
            maybe_ids = missing_func(phoneme)
            if maybe_ids:
                if append_list:
                    target.append(maybe_ids)
                else:
                    target.extend(maybe_ids)

    # Add beginning-of-sentence symbol
    if bos:
        maybe_extend_ids(bos, word_phoneme_ids)

    if blank_id is not None:
        # Blank token
        word_phoneme_ids.append([blank_id])

    for word in word_phonemes:
        word_ids: typing.List[int] = []

        if separate_graphemes:
            word = list(
                itertools.chain.from_iterable(
                    unicodedata.normalize("NFD", p) for p in word
                )
            )

        for phoneme in word:
            if separate_tones:
                # Separate tones (digits at the end of a phoneme)
                tone = []

                # Strip digits off the back of the phoneme (reversed)
                while phoneme and phoneme[-1].isdigit():
                    tone.append(phoneme[-1])
                    phoneme = phoneme[:-1]

                if tone:
                    tone = "".join(reversed(tone))
                    maybe_extend_ids(tone, word_ids, append_list=False)

            if is_separate is None:
                # No more splitting
                sub_phonemes = [phoneme]
            else:
                # Separate out stress, etc.
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

        if word_ids:
            if blank_id is None:
                # No blank phoneme
                word_phoneme_ids.append(word_ids)
            elif blank_between == BlankBetween.TOKENS:
                # Blank phoneme between each token
                word_phoneme_ids.append(
                    list(
                        # [p, blank, p, blank, ...]
                        itertools.chain.from_iterable(
                            # ((p, blank), (p, blank), ...)
                            itertools.zip_longest(
                                word_ids, itertools.repeat(blank_id, len(word_ids))
                            )
                        )
                    )
                )
            elif blank_between == BlankBetween.WORDS:
                # Blank phoneme between each word (list of tokens)
                word_phoneme_ids.append(word_ids)
                word_phoneme_ids.append([blank_id])
            else:
                raise ValueError(f"Unexpected value for blank_between: {blank_between}")

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
                tone = []

                # Strip digits off the back of the phoneme (reversed)
                while phoneme and phoneme[-1].isdigit():
                    tone.append(phoneme[-1])
                    phoneme = phoneme[:-1]

                if tone:
                    tone = "".join(reversed(tone))
                    all_phonemes.add(tone)
                    if all_phoneme_counts is not None:
                        all_phoneme_counts[tone] += 1

            if is_separate is None:
                # No more splitting
                sub_phonemes = [phoneme]
            else:
                # Separate out stress, etc.
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
