import itertools
import typing


def load_phoneme_ids(phonemes_file: typing.TextIO) -> typing.Dict[str, int]:
    # Format is ID<space>PHONEME
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
    # Format is FROM_PHONEME<space>TO_PHONEME
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


def partition(pred, iterable):
    "Use a predicate to partition entries into false entries and true entries"
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)
