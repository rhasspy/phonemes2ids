# phonemes2ids

Flexible tool for assigning integer ids to phonemes.

Useful for text to speech or speech to text applications where text is phonemized, converted to an integer vector, and then used to train a network.

## Installation

phonemes2ids is available on PyPI:

```sh
pip install phonemes2ids
```

If installation was successful, you should be able to run:

```sh
phonemes2ids --version
```

## Learning Phoneme IDs

```sh
cat << EOF |
a b c
b a a b
EOF
  phonemes2ids --write-phonemes phonemes.txt
```

which prints out:

```
0 1 2
1 0 0 1
```

Looking at phonemes.txt, we get:

```
0 a
1 b
2 c
```

Importantly, the assignment of ids to phonemes is deterministic. It is based on the sorted order of the final observed phoneme set. So changing the order of our input lines:

```sh
cat << EOF |
b a a b
a b c
EOF
  phonemes2ids --write-phonemes phonemes.txt
```

does not change the ids associated with each phoneme:

```
1 0 0 1
0 1 2
```

### Pre-Assigned Phonemes

We can pre-assign ids to some (or all) phonemes beforehand, allowing the rest to be learned:

```sh
echo '0 c' > assigned_phonemes.txt
cat << EOF |
b a a b
a b c
EOF
  phonemes2ids --read-phonemes assigned_phonemes.txt \
               --write-phonemes phonemes.txt
```

The output is now:

```
2 1 1 2
1 2 0
```

and phonemes.txt shows the new assignments:

```
0 c
1 a
2 b
```

### Phoneme/Word Separators and Blanks

By default, phonemes are assumed to not be separated at all and words are separated by whitespace. Let's specify instead that phonemes are separated by a '_' and words a '|':

```sh
echo 'a|b|a_b|b_a' | phonemes2ids -p '_' -w '|'
0 1 0 1 1 0
```

where `a` is 0 and `b` is 1.

Word separators become especially useful when you want to insert blank tokens between words:

```sh
echo '0 #' > assigned_phonemes.txt
echo 'a|b|a_b|b_a' | \
    phonemes2ids -p '_' -w '|' --blank '#' \
                 --read-phonemes assigned_phonemes.txt
0 1 0 2 0 1 2 0 2 1 0
```

where `#` is 0, and `a` and `b` are 0 and 1 respectively. Note that `a_b` and `b_a` are surrounded by `#` (0) in the output because they are words.

Blank tokens are useful for some machine learning models, such as [GlowTTS](https://github.com/jaywalnut310/glow-tts/). They are inserted between words by default, including before the first word (change with `--no-blank-start`) and after the last word (change with `--no-blank-end`).

It's possible to include blank tokens between *every* phoneme (instead of just between words):

```sh
echo '0 #' > assigned_phonemes.txt
echo 'a|b|a_b|b_a' | \
    phonemes2ids -p '_' -w '|' --blank '#' --blank-between tokens \
                 --read-phonemes assigned_phonemes.txt
0 1 0 2 0 1 0 2 0 2 0 1 0
```

Now every other phoneme/token in the output is blank (`#` = 0).

### Pad/BOS/EOS Symbols

It's common to include pad, bos (beginning of sentence), and eos (end of sentence) symbols. These typically occupy the first few phoneme ids, especially the pad symbol which is almost always 0.

You can have bos/eos added automatically:

```sh
echo 'a b c' | \
    phonemes2ids --pad '_' --bos '^' --eos '$' \
                 --write-phonemes phonemes.txt
1 3 4 5 2
```

Looking at phonemes.txt, we can see that pad, bos, and eos are automatically assigned ids (in that order):

```
0 _
1 ^
2 $
3 a
4 b
5 c
```

The output from the first command (`1 3 4 5 2`) can now be interpreted as `^ a b c $`.

### Stress/Tone Separation

Depending on your use case, it may be important that stress markers and tones are separated into distinct phonemes.

By default, stress is assumed to be part of a phoneme:

```sh
echo "ˈa a cˌ c" | phonemes2ids -p ' '
3 0 2 1
```

Note that each phoneme as received a distinct id. To separate the IPA primary/secondary stress characters (U+02C8 and U+02CC):

```sh
echo "ˈa a cˌ c" | \
    phonemes2ids -p ' ' --separate-stress \
                 --write-phonemes phonemes.txt
0 2 2 3 1 3
```

Looking in phonemes.txt, we can see that stress markers are assigned ids first:

```
0 ˈ
1 ˌ
2 a
3 c
```

Tones can also be separated, if desired. These are represented as digits (`[0-9]+`) that follow a phoneme:

```sh
echo 'a123 b45 c6' | \
    phonemes2ids -p ' ' --separate-tones \
                 --write-phonemes phonemes.txt
3 0 4 1 5 2
```

The tones are given separate ids and placed after their corresponding phoneme (change with `--tone-before`):

```
0 123
1 45
2 6
3 a
4 b
5 c
```

### Advanced Separation

Separating out parts of phonemes can be controlled further with the `--separate-graphemes` flag and `--separate <string>` option.

The `--separate-graphemes` flag will case all Unicode characters to be decomposed into codepoints before being assigned ids:

```sh
echo 'ɑ̃' | \
    phonemes2ids --separate-graphemes
0 1
```

where U+0251 (`ɑ`) is 0 and U+0303 (nasal) is 1.

Specifying the exact graphemes to separate out is done with `--separate <string>` (one or more times):

```sh
echo 'aː' | \
    phonemes2ids --separate 'ː'
0 1
```

where `a` is 0 and `ː` is 1. If the separator occurs in the middle of a phoneme, the phoneme is split into three parts (before, separator, after):

```sh
echo 'aːb' | \
    phonemes2ids --separate 'ː'
0 2 1
```

where `a` is 0, `b` is 1, and `ː` is 2.

### Punctuation Simplification

If you only care about short and long pauses in a sentence, the `--simple-punctuation` flag is for you! It replaces common punctuation symbols with either `,` (short pause) or `.` (long pause):

```sh
echo ', . : ; ! ?' | \
    phonemes2ids --simple-punctuation
0 1 0 0 1 1
```

where `,` is 0 and `.` is 1. Use `--phoneme-map` for more control.

---

## Phoneme Counts and Maps

The learning feature of phonemes2ids can be used to help you reduce your phoneme set. A typical workflow is:

1. Run `phonemes2ids` with `--write-phoneme-counts` on your input data
2. Look inside the phoneme counts file, and decide which phonemes should be re-mapped (usually ones with very few examples)
3. Create a phoneme map text file, where each line is `<FROM> <TO>` like `ʌ ə` (every occurrence of `ʌ` is replaced by `ə`)
    * The `<TO>` can be multiple phonemes like `aɪ a ɪ`, which breaks apart the dipthong
4. Re-run `phonemes2ids` with `--phoneme-map` and `--write-phonemes`

Make sure to keep your phoneme map with your phonemes.txt file!

---

## Converting Phonemes to IDs

Once you've figured out all of your settings, it's time to convert some input data! This will usually look something like:

```sh
phonemes2ids --read-phonemes phonemes.txt \
             --phoneme-map map.txt \
             [other settings] \
             < input_phonemes.txt \
             > output_ids.txt
```

where `phonemes.txt` contains your complete phoneme/id pairs from the learning phase, and `map.txt` has phoneme/phoneme pairs that you'd like to be automatically replaced.
Each line in the output file (`output_ids.txt`) will contain the ids of the corresponding line from the input file (`input_phonemes.txt`).

If your input file is delimited, you can keep extra information with each output line:

```sh
echo 's1|a b c' | phonemes2ids --csv
s1|a b c|0 1 2
```

The `--csv` flag indicates that the input data is delimited by '|' (change with `--csv-delimiter`). The final column of each row is assumed to be the input phonemes, and the ids are simply appended as a new column. This allows you to pass arbitrary metadata through to the output file.

---

## Python Library

You can use phonemes2ids directly from Python:

```python
from phonemes2ids import phonemes2ids

word_phonemes = [["a"], ["b"], ["c"], ["b", "c", "a"]]
phoneme_to_id = {"a": 1, "b": 2, "c": 3}

ids = phonemes2ids(word_phonemes=word_phonemes, phoneme_to_id=phoneme_to_id)

assert ids == [1, 2, 3, 2, 3, 1]
```

See the docstrings for `phonemes2ids` and `learn_phoneme_ids` for more details.
