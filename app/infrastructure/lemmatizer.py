import os
from collections import Counter
from functools import lru_cache

from mawo_pymorphy3 import create_analyzer
from razdel import tokenize

_morph_analyzer = None


def _get_analyzer():
    global _morph_analyzer
    if _morph_analyzer is None:
        _morph_analyzer = create_analyzer()

    return _morph_analyzer


class Pymorphy3LemmasCounter:
    def count_lemmas(self, text: str) -> dict[str, int]:
        counter = Counter()
        for token in tokenize(text):
            if token.text.isalpha():
                lemma = self._to_normal_form(token.text)
                counter[lemma] += 1

        return counter

    @lru_cache(maxsize=int(os.getenv("LEMMAS_CACHE_MAXSIZE", "0")))
    def _to_normal_form(self, word: str):
        morph = _get_analyzer()
        parses = morph.parse(word)
        if parses:
            return parses[0].normal_form

        return word
