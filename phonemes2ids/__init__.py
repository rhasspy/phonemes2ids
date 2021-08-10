import itertools
import logging
import typing

from .const import PUNCTUATION_MAP, STRESS, BlankBetween

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
    separate_stress: bool = False,
    stress: typing.Optional[typing.Collection[str]] = None,
    phoneme_map: typing.Optional[typing.Mapping[str, str]] = None,
) -> typing.List[int]:
    if phoneme_map is None:
        phoneme_map = {}

    assert phoneme_map is not None

    if punctuation_map is None:
        punctuation_map = PUNCTUATION_MAP

    assert punctuation_map is not None

    if stress is None:
        stress = STRESS

    assert stress is not None

    blank_id: typing.Optional[int] = None
    if blank:
        blank_id = phoneme_to_id[blank]

    # Transform into phoneme ids
    word_phoneme_ids = []

    # Add beginning-of-sentence symbol
    if bos:
        word_phoneme_ids.append([phoneme_to_id[bos]])

    if blank_id is not None:
        # Blank token
        word_phoneme_ids.append([blank_id])

    for word in word_phonemes:
        word_ids = []
        for phoneme in word:
            if separate_stress and stress:
                # Split stress out
                while phoneme and (phoneme[0] in stress):
                    stress_phoneme = phoneme_map.get(phoneme[0], phoneme[0])
                    word_ids.append(phoneme_to_id[stress_phoneme])
                    phoneme = phoneme[1:]

            if phoneme:
                if simple_punctuation and punctuation_map:
                    phoneme = punctuation_map.get(phoneme, phoneme)

                to_phonemes = phoneme_map.get(phoneme)
                if to_phonemes:
                    # Mapped to one or more phonemes
                    word_ids.extend(
                        (phoneme_to_id[to_phoneme] for to_phoneme in to_phonemes)
                    )
                else:
                    # No map
                    word_ids.append(phoneme_to_id[phoneme])

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
        word_phoneme_ids.append([phoneme_to_id[eos]])

    return list(itertools.chain.from_iterable(word_phoneme_ids))


# -----------------------------------------------------------------------------


def learn_phoneme_ids(
    word_phonemes: typing.List[typing.List[str]],
    all_phonemes: typing.Set[str],
    all_phoneme_counts: typing.Optional[typing.Counter[str]] = None,
    simple_punctuation: bool = False,
    punctuation_map: typing.Optional[typing.Mapping[str, str]] = None,
    separate_stress: bool = False,
    stress: typing.Optional[typing.Collection[str]] = None,
    phoneme_map: typing.Optional[typing.Mapping[str, str]] = None,
):
    if phoneme_map is None:
        phoneme_map = {}

    if punctuation_map is None:
        punctuation_map = PUNCTUATION_MAP

    if stress is None:
        stress = STRESS

    for word in word_phonemes:
        for phoneme in word:
            if separate_stress:
                # Split stress out
                while phoneme and (phoneme[0] in stress):
                    phoneme = phoneme[1:]

            if phoneme:
                if simple_punctuation:
                    phoneme = punctuation_map.get(phoneme, phoneme)

                to_phonemes = phoneme_map.get(phoneme)
                if to_phonemes:
                    # Mapped to one or more phonemes
                    for to_phoneme in to_phonemes:
                        all_phonemes.add(to_phoneme)

                        if all_phoneme_counts is not None:
                            all_phoneme_counts[to_phoneme] += 1
                else:
                    # No map
                    all_phonemes.add(phoneme)

                    if all_phoneme_counts is not None:
                        all_phoneme_counts[phoneme] += 1
