"""
DynamoDB Models
"""

from typing import Any, Mapping, NotRequired, Sequence, TypedDict


class AttributeValueTypeDef(TypedDict):
    """
    Type definition for DynamoDB AttributeValue format.

    Each key in a DynamoDB item can only contain one of these types
    From:
        mypy_boto3_dynamodb/type_defs.pyi
    """

    S: NotRequired[str]
    N: NotRequired[str]
    B: NotRequired[bytes]
    SS: NotRequired[Sequence[str]]
    NS: NotRequired[Sequence[str]]
    BS: NotRequired[Sequence[bytes]]
    M: NotRequired[Mapping[str, Any]]
    L: NotRequired[Sequence[Any]]
    NULL: NotRequired[bool]
    BOOL: NotRequired[bool]
