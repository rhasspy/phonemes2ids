"""Command-line interface to phonemes2ids"""
import argparse
import csv
import logging
import os
import sys
import typing
from collections import Counter

from . import learn_phoneme_ids, phonemes2ids
from .const import PUNCTUATION_MAP, STRESS, BlankBetween
from .utils import load_phoneme_ids, load_phoneme_map

_LOGGER = logging.getLogger("phonemes2ids")

# -----------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(prog="phonemes2ids")
    parser.add_argument(
        "--write-phonemes", help="Path to write phoneme ids text file (ID PHONEME)"
    )
    parser.add_argument(
        "--read-phonemes", help="Read phoneme ids from a text file (ID PHONEME)"
    )
    parser.add_argument(
        "-p", "--phoneme-separator", help="Separator character between phonemes"
    )
    parser.add_argument(
        "-w", "--word-separator", default=" ", help="Separator character between words"
    )
    parser.add_argument(
        "--id-separator", default=" ", help="Separator string each phoneme id"
    )
    parser.add_argument("--pad", help="Phoneme for padding (phoneme 0)")
    parser.add_argument("--bos", help="Phoneme to put at beginning of sentence")
    parser.add_argument("--eos", help="Phoneme to put at end of sentence")
    parser.add_argument(
        "--blank", help="Phoneme to put between words or tokens (see --blank-between)"
    )
    parser.add_argument(
        "--blank-between",
        choices=[v.value for v in BlankBetween],
        default=BlankBetween.WORDS,
        help="Where to insert blank phoneme (default: words)",
    )
    parser.add_argument(
        "--no-blank-start",
        action="store_true",
        help="Don't insert a blank token before the first word/token",
    )
    parser.add_argument(
        "--no-blank-end",
        action="store_true",
        help="Don't insert a blank token after the last word/token",
    )
    parser.add_argument(
        "--simple-punctuation",
        action="store_true",
        help="Map all punctuation into ',' and '.'",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Input and output is CSV. Phonemes ids are added as a final column",
    )
    parser.add_argument(
        "--csv-delimiter", default="|", help="Delimiter in CSV input and output"
    )
    parser.add_argument(
        "--output-separator",
        default="|",
        help="Separator string between input phonemes and phoneme ids",
    )
    parser.add_argument(
        "--print-input", action="store_true", help="Print input text before phoneme ids"
    )
    parser.add_argument(
        "--separate-stress",
        action="store_true",
        help="Pull primary/secondary stress out as separate phonemes",
    )
    parser.add_argument(
        "--stress",
        action="append",
        help="Add phoneme to consider as stress (overwrites default of ˈˌ)",
    )
    parser.add_argument(
        "--separate-graphemes",
        action="store_true",
        help="Break apart graphemes into individual codepoints for phonemes",
    )
    parser.add_argument(
        "--separate-tones",
        action="store_true",
        help="Break apart tones (digits at the end of a phoneme) into individual phonemes",
    )
    parser.add_argument(
        "--tone-before",
        action="store_true",
        help="Insert separated tones before their corresponding phoneme instead of after",
    )
    parser.add_argument(
        "--separate",
        action="append",
        help="Break apart provided grapheme into separate phoneme",
    )
    parser.add_argument(
        "--write-phoneme-counts", help="Path to write phoneme counts observed in input"
    )
    parser.add_argument(
        "-m",
        "--map",
        nargs=2,
        action="append",
        help="Map from observed phoneme to desired phonemes",
    )
    parser.add_argument(
        "--phoneme-map",
        help="Path to text file with FROM_PHONEME TO_PHONEME on each line",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # -------------------------------------------------------------------------

    if args.version:
        # Print version and exit
        from . import __version__

        print(__version__)
        sys.exit(0)

    # Map from observed phoneme to desired phonemes(s)
    phoneme_map: typing.Dict[str, typing.List[str]] = {}
    if args.phoneme_map:
        with open(args.phoneme_map, "r") as phoneme_map_file:
            phoneme_map = load_phoneme_map(phoneme_map_file)

    if args.map:
        # Extra mappings from command line
        for from_phoneme, to_phonemes in args.map:
            if not to_phonemes.strip():
                # Whitespace
                phoneme_map[from_phoneme] = [" "]
            else:
                # Not whitespace
                phoneme_map[from_phoneme] = to_phonemes.split()

    phoneme_to_id: typing.Dict[str, int] = {}

    if args.read_phonemes:
        # Load from phonemes file
        # Format is ID<space>PHONEME
        with open(args.read_phonemes, "r") as phonemes_file:
            phoneme_to_id.update(load_phoneme_ids(phonemes_file))

    if args.pad and (args.pad not in phoneme_to_id):
        # Add pad symbol
        phoneme_to_id[args.pad] = len(phoneme_to_id)

    if args.bos and (args.bos not in phoneme_to_id):
        # Add BOS symbol
        phoneme_to_id[args.bos] = len(phoneme_to_id)

    if args.eos and (args.eos not in phoneme_to_id):
        # Add EOS symbol
        phoneme_to_id[args.eos] = len(phoneme_to_id)

    if args.blank and (args.blank not in phoneme_to_id):
        # Add blank symbol
        phoneme_to_id[args.blank] = len(phoneme_to_id)

    separate: typing.Set[str] = set()
    if args.separate:
        separate.update(args.separate)

    if args.separate_stress:
        # Add stress symbols
        for stress in sorted(STRESS):
            separate.add(stress)
            if stress not in phoneme_to_id:
                phoneme_to_id[stress] = len(phoneme_to_id)

    # -------------------------------------------------------------------------

    if os.isatty(sys.stdin.fileno()):
        print("Reading phonemes from stdin...", file=sys.stderr)

    # CSV input/output
    if args.csv:
        csv_writer = csv.writer(sys.stdout, delimiter=args.csv_delimiter)
        reader = csv.reader(sys.stdin, delimiter=args.csv_delimiter)
    else:
        csv_writer = None
        reader = sys.stdin

    # Read all input and get set of phonemes
    all_phonemes = set(phoneme_to_id.keys())
    all_phoneme_counts = Counter()

    if args.simple_punctuation:
        # Add , and .
        all_phonemes.update(sorted(PUNCTUATION_MAP.values()))

    lines = []

    for line in reader:
        if args.csv:
            phonemes_str = line[-1]
        else:
            phonemes_str = line.strip()
            if not phonemes_str:
                continue

        # Split into words
        if args.phoneme_separator:
            word_phonemes = [
                word.split(args.phoneme_separator)
                for word in phonemes_str.split(args.word_separator)
            ]
        else:
            word_phonemes = [
                list(word) for word in phonemes_str.split(args.word_separator)
            ]

        lines.append((line, word_phonemes))

        # Accumulate phoneme set and counts
        learn_phoneme_ids(
            word_phonemes,
            all_phonemes,
            all_phoneme_counts=all_phoneme_counts,
            simple_punctuation=args.simple_punctuation,
            separate=separate,
            separate_graphemes=args.separate_graphemes,
            separate_tones=args.separate_tones,
            phoneme_map=phoneme_map,
        )

    # Assign phonemes to ids in sorted order
    for phoneme in sorted(all_phonemes):
        if phoneme not in phoneme_to_id:
            phoneme_to_id[phoneme] = len(phoneme_to_id)

    # -------------------------------------------------------------------------

    for line, word_phonemes in lines:
        if args.csv:
            phonemes_str = line[-1]
        else:
            phonemes_str = line.strip()

        # Transform into phoneme ids
        word_phoneme_ids = phonemes2ids(
            word_phonemes,
            phoneme_to_id=phoneme_to_id,
            pad=args.pad,
            bos=args.bos,
            eos=args.eos,
            blank=args.blank,
            blank_between=args.blank_between,
            blank_at_start=(not args.no_blank_start),
            blank_at_end=(not args.no_blank_end),
            simple_punctuation=args.simple_punctuation,
            separate=separate,
            separate_graphemes=args.separate_graphemes,
            separate_tones=args.separate_tones,
            tone_before=args.tone_before,
            phoneme_map=phoneme_map,
        )

        phoneme_ids_str = args.id_separator.join(
            (str(p_id) for p_id in word_phoneme_ids)
        )

        if args.csv:
            # Add phoneme ids as last column
            assert csv_writer is not None
            csv_writer.writerow((*line, phoneme_ids_str))
        else:
            if args.print_input:
                # Print input phonemes as well as phoneme ids
                print(phonemes_str, phoneme_ids_str, sep=args.output_separator)
            else:
                # Just print phoneme ids
                print(phoneme_ids_str)

    # -------------------------------------------------------------------------

    if args.write_phonemes:
        # Write file with ID<space>PHONEME format
        if args.write_phonemes == "-":
            print("")
            write_phoneme_ids(phoneme_to_id)
        else:
            # Write to file
            with open(args.write_phonemes, "w") as phonemes_file:
                write_phoneme_ids(phoneme_to_id, phonemes_file)

    if args.write_phoneme_counts:
        # Write file with PHONEME<space>COUNT format
        if args.write_phoneme_counts == "-":
            print("")
            write_phoneme_counts(all_phoneme_counts)
        else:
            with open(args.write_phoneme_counts, "w") as counts_file:
                write_phoneme_counts(all_phoneme_counts, counts_file)


# -----------------------------------------------------------------------------


def write_phoneme_ids(
    phoneme_to_id: typing.Mapping[str, int],
    phonemes_file: typing.Optional[typing.TextIO] = None,
):
    for phoneme, phoneme_id in sorted(phoneme_to_id.items(), key=lambda kv: kv[1]):
        print(phoneme_id, phoneme, file=phonemes_file)


def write_phoneme_counts(
    phoneme_counts: typing.Counter[str],
    counts_file: typing.Optional[typing.TextIO] = None,
):
    for phoneme, phoneme_count in phoneme_counts.most_common():
        print(phoneme, phoneme_count, file=counts_file)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
