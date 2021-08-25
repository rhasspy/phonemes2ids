#!/usr/bin/env python3
"""Tests for learn_phoneme_ids"""
import unittest
from collections import Counter

from phonemes2ids import learn_phoneme_ids


class LearnPhonemeIdsTestCase(unittest.TestCase):
    """Test cases for learn_phoneme_ids"""

    def test_abc(self):
        """Test basic learning"""
        word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
        all_phonemes = set()
        phoneme_counts = Counter()

        learn_phoneme_ids(
            word_phonemes=word_phonemes,
            all_phonemes=all_phonemes,
            all_phoneme_counts=phoneme_counts,
        )

        self.assertEqual(all_phonemes, {"a", "b", "c"})

        # Verify counts
        self.assertEqual(len(phoneme_counts), 3)

        for p in all_phonemes:
            self.assertEqual(phoneme_counts[p], 2)

    def test_simple_punctuation(self):
        """Test punctuation replacement with short/long pauses (,/.)"""
        word_phonemes = [[".", ",", ";", "!", "?"]]
        all_phonemes = set()

        # Without simple punctuation
        learn_phoneme_ids(word_phonemes=word_phonemes, all_phonemes=all_phonemes)
        self.assertEqual(all_phonemes, set(word_phonemes[0]))

        # With simple punctuation
        all_phonemes = set()
        learn_phoneme_ids(
            word_phonemes=word_phonemes,
            all_phonemes=all_phonemes,
            simple_punctuation=True,
        )
        self.assertEqual(all_phonemes, {",", "."})  # short/long pause

    def test_separate_graphemes(self):
        """Test grapheme separation (ɑ̃ -> \u0251, \u0303)"""
        word_phonemes = [["ɑ̃", "t͡ʃ"]]
        all_phonemes = set()

        # Without separate graphemes
        learn_phoneme_ids(word_phonemes=word_phonemes, all_phonemes=all_phonemes)
        self.assertEqual(all_phonemes, set(word_phonemes[0]))

        # With separate graphemes
        all_phonemes = set()
        learn_phoneme_ids(
            word_phonemes=word_phonemes,
            all_phonemes=all_phonemes,
            separate_graphemes=True,
        )
        self.assertEqual(all_phonemes, {"ɑ", "\u0303", "t", "\u0361", "ʃ"})

    def test_separate_tones(self):
        """Test tone separation (a1 -> a, 1)"""
        word_phonemes = [["a1", "b234"]]
        all_phonemes = set()

        # Without separate tones
        learn_phoneme_ids(word_phonemes=word_phonemes, all_phonemes=all_phonemes)
        self.assertEqual(all_phonemes, set(word_phonemes[0]))

        # With separate tones
        all_phonemes = set()
        learn_phoneme_ids(
            word_phonemes=word_phonemes, all_phonemes=all_phonemes, separate_tones=True
        )
        self.assertEqual(all_phonemes, {"a", "b", "1", "234"})

    def test_separate_stress(self):
        """Test stress separation (ˈa -> ˈ, a)"""
        word_phonemes = [["ˈa", "ˌb"]]
        all_phonemes = set()

        # Without separate stress
        learn_phoneme_ids(word_phonemes=word_phonemes, all_phonemes=all_phonemes)
        self.assertEqual(all_phonemes, set(word_phonemes[0]))

        # With separate stress
        all_phonemes = set()
        learn_phoneme_ids(
            word_phonemes=word_phonemes, all_phonemes=all_phonemes, separate=["ˈ", "ˌ"]
        )
        self.assertEqual(all_phonemes, {"ˈ", "a", "ˌ", "b"})

    def test_phoneme_map(self):
        """Test phoneme mapping"""
        word_phonemes = [["a", "c"]]
        all_phonemes = set()

        # Without phoneme map
        learn_phoneme_ids(word_phonemes=word_phonemes, all_phonemes=all_phonemes)
        self.assertEqual(all_phonemes, set(word_phonemes[0]))

        # With phoneme map
        all_phonemes = set()
        learn_phoneme_ids(
            word_phonemes=word_phonemes,
            all_phonemes=all_phonemes,
            phoneme_map={"a": "b", "c": "b"},
        )
        self.assertEqual(all_phonemes, {"b"})


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
