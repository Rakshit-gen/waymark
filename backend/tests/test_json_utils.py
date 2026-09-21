import pytest

from backend.json_utils import parse_json_response


def test_plain_json():
    assert parse_json_response('[{"a": 1}]') == [{"a": 1}]


def test_fenced_json():
    assert parse_json_response('```json\n{"a": 1}\n```') == {"a": 1}


def test_json_surrounded_by_prose():
    text = 'Here are the decisions:\n[{"claim": "x"}]\nHope that helps.'
    assert parse_json_response(text) == [{"claim": "x"}]


def test_skips_stray_bracket_before_real_json():
    assert parse_json_response('Note [see below]: {"ok": true}') == {"ok": True}


def test_no_json_raises_value_error():
    with pytest.raises(ValueError):
        parse_json_response("I could not find any decisions.")
