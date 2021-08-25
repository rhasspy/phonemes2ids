#!/usr/bin/env python3
"""Tests for phonemes2ids"""
import unittest
from collections import Counter

from phonemes2ids import phonemes2ids, BlankBetween


class Phoneme2IdsTestCase(unittest.TestCase):
    """Test cases for phonemes2ids"""

    def test_basic(self):
        """Test basic mapping"""
        word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
        phoneme_to_id = {"a": 1, "b": 2, "c": 3}

        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)

        self.assertEqual(ids, [1, 2, 3, 2, 3, 1])

    def test_blank_between_words(self):
        """Test blank symbol between words"""
        word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
        blank = "#"
        phoneme_to_id = {"a": 1, "b": 2, "c": 3, blank: 4}

        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            blank=blank,
            blank_between=BlankBetween.WORDS,
        )

        # between words
        self.assertEqual(ids, [4, 1, 4, 2, 4, 3, 4, 2, 3, 1, 4])

        # No blanks at start/end
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            blank=blank,
            blank_between=BlankBetween.WORDS,
            blank_at_start=False,
            blank_at_end=False,
        )

        self.assertEqual(ids, [1, 4, 2, 4, 3, 4, 2, 3, 1])

    def test_blank_between_tokens(self):
        """Test blank symbol between tokens"""
        word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
        blank = "#"
        phoneme_to_id = {"a": 1, "b": 2, "c": 3, blank: 4}

        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            blank=blank,
            blank_between=BlankBetween.TOKENS,
        )

        # between every phoneme (token)
        self.assertEqual(ids, [4, 1, 4, 2, 4, 3, 4, 2, 4, 3, 4, 1, 4])

        # No blanks at start/end
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            blank=blank,
            blank_between=BlankBetween.TOKENS,
            blank_at_start=False,
            blank_at_end=False,
        )

        self.assertEqual(ids, [1, 4, 2, 4, 3, 4, 2, 4, 3, 4, 1])

    def test_bos_eos(self):
        """Test bos/eos symbols"""
        word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
        bos = "^"
        eos = "$"
        phoneme_to_id = {"a": 1, "b": 2, "c": 3, bos: 4, eos: 5}

        ids = phonemes2ids(
            word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id, bos=bos, eos=eos
        )

        self.assertEqual(ids, [4, 1, 2, 3, 2, 3, 1, 5])

    def test_simple_punctuation(self):
        """Test punctuation replacement with short/long pauses (,/.)"""
        word_phonemes = [[".", ",", ";", "!", "?"]]
        phoneme_to_id = {".": 1, ",": 2, ";": 3, "!": 4, "?": 5}

        # Without simple punctuation
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 2, 3, 4, 5])

        # With simple punctuation
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            simple_punctuation=True,
        )

        # ; -> ,
        # !/? -> .
        self.assertEqual(ids, [1, 2, 2, 1, 1])

    def test_separate_graphemes(self):
        """Test grapheme separation (ɑ̃ -> \u0251, \u0303)"""
        word_phonemes = [["ɑ̃", "t͡ʃ"]]
        phoneme_to_id = {
            "ɑ̃": 1,
            "t͡ʃ": 2,
            "ɑ": 3,
            "\u0303": 4,
            "t": 5,
            "\u0361": 6,
            "ʃ": 7,
        }

        # Without separate graphemes
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 2])

        # With separate graphemes
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            separate_graphemes=True,
        )
        self.assertEqual(ids, [3, 4, 5, 6, 7])

    def test_separate_tones(self):
        """Test tone separation (a1 -> a, 1)"""
        word_phonemes = [["a1", "b234"]]
        phoneme_to_id = {"a1": 1, "b234": 2, "a": 3, "1": 4, "b": 5, "234": 6}

        # Without separate tones
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 2])

        # With separate tones
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            separate_tones=True,
        )
        self.assertEqual(ids, [3, 4, 5, 6])

        # With separate tones (before phonemes: a1 -> 1, a)
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            separate_tones=True,
            tone_before=True,
        )
        self.assertEqual(ids, [4, 3, 6, 5])

    def test_separate_stress(self):
        """Test stress separation (ˈa -> ˈ, a)"""
        word_phonemes = [["ˈa", "ˌb"]]
        phoneme_to_id = {"ˈa": 1, "ˌb": 2, "ˈ": 3, "a": 4, "ˌ": 5, "b": 6}

        # Without separate stress
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 2])

        # With separate stress
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            separate=["ˈ", "ˌ"],
        )
        self.assertEqual(ids, [3, 4, 5, 6])

    def test_phoneme_map(self):
        """Test phoneme mapping"""
        word_phonemes = [["a", "c"]]
        phoneme_to_id = {"a": 1, "b": 2, "c": 3}

        # Without phoneme map
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 3])

        # With phoneme map
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            phoneme_map={"a": "b", "c": "b"},
        )
        self.assertEqual(ids, [2, 2])

    def test_missing_func(self):
        """Test function for determining missing ids"""
        word_phonemes = [["a", "b", "c"]]
        phoneme_to_id = {"_": 0, "a": 1, "c": 2}

        def missing_func(p):
            # ids for missing phoneme
            return [0]

        # Without missing func
        ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)
        self.assertEqual(ids, [1, 2])

        # With missing func
        ids = phonemes2ids(
            word_phonemes=word_phonemes,
            phoneme_to_id=phoneme_to_id,
            missing_func=missing_func,
        )
        self.assertEqual(ids, [1, 0, 2])


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
