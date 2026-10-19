import json

import pytest

from app.llm.base import LLMError, _extract_json


def test_truncated_object_does_not_return_nested_array():
    with pytest.raises(LLMError):
        _extract_json('{"objectives": ["Learn"], "content_markdown": "unfinished')


def test_json_containing_markdown_fences_is_preserved():
    lesson = {"content_markdown": 'Example:\n```json\n["example"]\n```'}
    assert _extract_json(json.dumps(lesson)) == lesson


@pytest.mark.parametrize("text, expected", [
    ('```json\n{"title": "Lesson"}\n```', {"title": "Lesson"}),
    ('Here is the JSON: {"title": "Lesson"} Done.', {"title": "Lesson"}),
    ('[1, 2]', [1, 2]),
])
def test_extract_complete_json(text, expected):
    assert _extract_json(text) == expected
