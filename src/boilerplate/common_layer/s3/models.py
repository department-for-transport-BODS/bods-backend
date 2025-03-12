"""
S3 Client Models
(Generally Taken from mypy)
"""

from datetime import datetime
from typing import Literal, NotRequired, TypedDict

ChecksumAlgorithmType = Literal["CRC32", "CRC32C", "SHA1", "SHA256"]
ObjectStorageClassType = Literal[
    "DEEP_ARCHIVE",
    "EXPRESS_ONEZONE",
    "GLACIER",
    "GLACIER_IR",
    "INTELLIGENT_TIERING",
    "ONEZONE_IA",
    "OUTPOSTS",
    "REDUCED_REDUNDANCY",
    "SNOW",
    "STANDARD",
    "STANDARD_IA",
]


class RestoreStatusTypeDef(TypedDict):
    """S3 object restore status information."""

    IsRestoreInProgress: NotRequired[bool]
    RestoreExpiryDate: NotRequired[datetime]


class OwnerTypeDef(TypedDict):
    """S3 object owner information."""

    DisplayName: NotRequired[str]
    ID: NotRequired[str]


class ObjectTypeDef(TypedDict):
    """S3 object metadata."""

    Key: NotRequired[str]
    LastModified: NotRequired[datetime]
    ETag: NotRequired[str]
    ChecksumAlgorithm: NotRequired[list[ChecksumAlgorithmType]]
    Size: NotRequired[int]
    StorageClass: NotRequired[ObjectStorageClassType]
    Owner: NotRequired[OwnerTypeDef]
    RestoreStatus: NotRequired[RestoreStatusTypeDef]


class ResponseMetadataTypeDef(TypedDict):
    """S3 API response metadata."""

    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]


class CommonPrefixTypeDef(TypedDict):
    """S3 common prefixes in list operations."""

    Prefix: NotRequired[str]


class ListObjectsV2OutputTypeDef(TypedDict):
    """S3 ListObjectsV2 operation response."""

    IsTruncated: bool
    Name: str
    Prefix: str
    Delimiter: str
    MaxKeys: int
    EncodingType: Literal["url"]
    KeyCount: int
    ContinuationToken: str
    NextContinuationToken: str
    StartAfter: str
    RequestCharged: Literal["requester"]
    ResponseMetadata: ResponseMetadataTypeDef
    Contents: NotRequired[list[ObjectTypeDef]]
    CommonPrefixes: NotRequired[list[CommonPrefixTypeDef]]
