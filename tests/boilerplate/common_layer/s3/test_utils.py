import pytest
from common_layer.s3.utils import get_filename_from_object_key


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
def test_get_filename_from_object_key(s3_object_key, expected_result):
    assert get_filename_from_object_key(s3_object_key) == expected_result
