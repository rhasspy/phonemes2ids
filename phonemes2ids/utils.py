"""Utility methods for phonemes2ids"""
import typing


def load_phoneme_ids(phonemes_file: typing.TextIO) -> typing.Dict[str, int]:
    """
    Load phoneme id mapping from a text file.
    Format is ID<space>PHONEME
    Comments start with #

    Args:
        phonemes_file: text file

    Returns:
        dict with phoneme -> id
    """
    phoneme_to_id = {}
    for line in phonemes_file:
        line = line.strip("\r\n")
        if (not line) or line.startswith("#") or (" " not in line):
            # Exclude blank lines, comments, or malformed lines
            continue

        phoneme_id, phoneme_str = line.split(" ", maxsplit=1)
        phoneme_to_id[phoneme_str] = int(phoneme_id)

    return phoneme_to_id


def load_phoneme_map(
    phoneme_map_file: typing.TextIO,
) -> typing.Dict[str, typing.List[str]]:
    """
    Load phoneme/phoneme mapping from a text file.
    Format is FROM_PHONEME<space>TO_PHONEME[<space>TO_PHONEME...]
    Comments start with #

    Args:
        phoneme_map_file: text file

    Returns:
        dict with from_phoneme -> [to_phoneme, to_phoneme, ...]
    """
    phoneme_map = {}
    for line in phoneme_map_file:
        line = line.strip("\r\n")
        if (not line) or line.startswith("#") or (" " not in line):
            # Exclude blank lines, comments, or malformed lines
            continue

        from_phoneme, to_phonemes_str = line.split(" ", maxsplit=1)
        if not to_phonemes_str.strip():
            # To whitespace
            phoneme_map[from_phoneme] = [" "]
        else:
            # To one or more non-whitespace phonemes
            phoneme_map[from_phoneme] = to_phonemes_str.split()

    return phoneme_map
