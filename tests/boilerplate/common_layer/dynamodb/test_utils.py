import pytest
from common_layer.dynamodb.utils import deserialize_dynamo_item, serialize_dynamo_item


@pytest.mark.parametrize(
    "input_data, expected",
    [
        ("test-string", {"S": "test-string"}),  # String
        (123, {"N": "123"}),  # Integer
        (45.67, {"N": "45.67"}),  # Float
        (True, {"BOOL": True}),  # Boolean
        (None, {"NULL": True}),  # Null
        (b"test bytes", {"B": b"test bytes"}),  # Bytes
    ],
)
def test_serialize_dynamo_item_from_simple_type(input_data, expected):
    assert serialize_dynamo_item(input_data) == expected


def test_serialize_dynamo_item_from_complex_type():
    input_data = {"key": "value", "nested": {"inner_key": 123, "flag": True}}
    expected_output = {
        "M": {
            "key": {"S": "value"},
            "nested": {"M": {"inner_key": {"N": "123"}, "flag": {"BOOL": True}}},
        }
    }
    assert serialize_dynamo_item(input_data) == expected_output

    input_list = ["test-string", 42, {"key": "value"}]
    expected_list_output = {
        "L": [{"S": "test-string"}, {"N": "42"}, {"M": {"key": {"S": "value"}}}]
    }
    assert serialize_dynamo_item(input_list) == expected_list_output


@pytest.mark.parametrize(
    "dynamo_item, expected",
    [
        ({"S": "test-string"}, "test-string"),  # String
        ({"N": "123"}, 123),  # Integer
        ({"N": "45.67"}, 45.67),  # Float
        ({"BOOL": True}, True),  # Boolean
        ({"NULL": True}, None),  # Null
        ({"B": b"test bytes"}, b"test bytes"),  # Bytes
    ],
)
def test_deserialize_dynamo_item_to_simple_type(dynamo_item, expected):
    assert deserialize_dynamo_item(dynamo_item) == expected


def test_deserialize_dynamo_item_to_complex_type():
    input_data = {
        "M": {
            "key": {"S": "value"},
            "nested": {"M": {"inner_key": {"N": "123"}, "flag": {"BOOL": True}}},
        }
    }
    expected_output = {"key": "value", "nested": {"inner_key": 123, "flag": True}}
    assert deserialize_dynamo_item(input_data) == expected_output

    input_list = {"L": [{"S": "test-string"}, {"N": "42"}, {"M": {"key": {"S": "value"}}}]}
    expected_list_output = ["test-string", 42, {"key": "value"}]
    assert deserialize_dynamo_item(input_list) == expected_list_output
