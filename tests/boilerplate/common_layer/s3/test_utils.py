"""
S3 Client Utils Tests
"""

import pytest
from common_layer.s3.utils import format_s3_tags, get_filename_from_object_key


@pytest.mark.parametrize(
    "s3_object_key,expected_result",
    [
        pytest.param(
            "/some/nested/object/key/filename_with_underscores.xml",
            "filename_with_underscores.xml",
            id="Nested object key",
        ),
        pytest.param(
            "filename_no_slashes.xml",
            "filename_no_slashes.xml",
            id="Object key without nesting",
        ),
        pytest.param("", None, id="Empty string"),
    ],
)
def test_get_filename_from_object_key(s3_object_key: str, expected_result: str | None):
    """
    Test Getting Filename of an object key correctly
    """
    assert get_filename_from_object_key(s3_object_key) == expected_result


@pytest.mark.parametrize(
    "tags_dict,expected_result",
    [
        pytest.param(
            {"env": "production", "owner": "data-team"},
            "env=production&owner=data-team",
            id="Simple key-value pairs",
        ),
        pytest.param(
            {"key with space": "value with space", "special/chars": "a+b=c?"},
            "key%20with%20space=value%20with%20space&special/chars=a%2Bb%3Dc%3F",
            id="Special characters needing encoding",
        ),
        pytest.param(
            {},
            None,
            id="Empty dictionary",
        ),
        pytest.param(
            None,
            None,
            id="None input",
        ),
        pytest.param(
            {"empty": "", "normal": "value"},
            "empty=&normal=value",
            id="Dictionary with empty string value",
        ),
        pytest.param(
            {"tag1": "123", "tag2": "456"},
            "tag1=123&tag2=456",
            id="Numeric values as strings",
        ),
    ],
)
def test_format_s3_tags(tags_dict: dict[str, str] | None, expected_result: str | str):
    """
    Test formatting tag dictionaries into S3-compatible URL-encoded strings
    """
    assert format_s3_tags(tags_dict) == expected_result
