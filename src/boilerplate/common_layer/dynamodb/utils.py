from typing import Any, Dict


def serialize_dynamo_item(raw: Any) -> Dict[str, Any]:
    """
    Serializes plain value/dict into DynamoDB item format.

    Example: 
        input: {"key": "value"}
        output: {"M": {"key": {"S": "value"}}}
    """ 
    if isinstance(raw, dict):
        return {"M": {key: serialize_dynamo_item(value) for key, value in raw.items()}}
    elif isinstance(raw, list):
        return {"L": [serialize_dynamo_item(value) for value in raw]}
    elif isinstance(raw, str):
        return {"S": raw}
    elif isinstance(raw, bool):
        return {"BOOL": raw}
    elif isinstance(raw, (int, float)):
        return {"N": str(raw)}
    elif isinstance(raw, bytes):
        return {"B": raw}
    elif raw is None:
        return {"NULL": True}
    else:
        raise ValueError(f"Unsupported type for DynamoDB conversion: {type(raw)}")

def deserialize_dynamo_item(item: Dict[str, Any]) -> Any:
    """
    Deserializes DynamoDB item format dict to a plain value/dict.

    Example: 
        input: {"M": {"key": {"S": "value"}}}
        output: {"key": "value"}
    """
    if "M" in item:
        return {key: deserialize_dynamo_item(value) for key, value in item["M"].items()}
    elif "L" in item:
        return [deserialize_dynamo_item(value) for value in item["L"]]
    elif "S" in item:
        return item["S"]
    elif "BOOL" in item:
        return item["BOOL"]
    elif "N" in item:
        return int(item["N"]) if item["N"].isdigit() else float(item["N"])
    elif "B" in item:
        return item["B"]
    elif "NULL" in item:
        return None
    else:
        raise ValueError(f"Unsupported DynamoDB type: {item}")


