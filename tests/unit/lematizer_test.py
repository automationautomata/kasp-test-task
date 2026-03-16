import importlib
import os
from typing import NamedTuple
from app.infrastructure import lemmatizer

import pytest


class DummyParse(NamedTuple):
    normal_form: str


class DummyToken(NamedTuple):
    text: str


@pytest.fixture
def mock_morph(mocker):
    return mocker.Mock()


@pytest.mark.parametrize(
    "text,tokens,normal_forms,expected_counts,parse_calls",
    [
        (
            "HELLO hello",
            ["HELLO", "hello"],
            ["hello", "hello"],
            {"hello": 2},
            2,
        ),
        (
            "!!! pytest, unittest",
            ["pytest", "unittest"],
            ["pytest", "unittest"],
            {"pytest": 1, "unittest": 1},
            2,
        ),
    ],
)
def test_count_lemmas(
    monkeypatch, mock_morph, text, tokens, normal_forms, expected_counts, parse_calls
):

    mock_morph.parse.side_effect = ([DummyParse(word)] for word in normal_forms)
    monkeypatch.setattr(
        "app.infrastructure.lemmatizer.tokenize", lambda _: map(DummyToken, tokens)
    )
    monkeypatch.setattr(
        "app.infrastructure.lemmatizer.get_worker_analyzer", lambda: mock_morph
    )

    counter = lemmatizer.Pymorphy3LemmasCounter()
    result = counter.count_lemmas(text)

    assert result == expected_counts
    assert mock_morph.parse.call_count == parse_calls


def test_lru_cache_behavior(monkeypatch, mock_morph):
    cache_size = 2

    os.environ["APP_LEMMAS_CACHE_MAXSIZE"] = str(cache_size)
    importlib.reload(lemmatizer)
    monkeypatch.setattr(
        "app.infrastructure.lemmatizer.get_worker_analyzer", lambda: mock_morph
    )
    counter = lemmatizer.Pymorphy3LemmasCounter()

    mock_morph.parse.side_effect = lambda word: [DummyParse(word.lower())]

    counter._to_normal_form("Hello")
    counter._to_normal_form("Hello")
    counter._to_normal_form("Hello")

    counter._to_normal_form("world")
    counter._to_normal_form("world")
    assert mock_morph.parse.call_count == 2
