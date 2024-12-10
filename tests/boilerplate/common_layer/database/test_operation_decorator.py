from unittest.mock import Mock

import pytest
from common_layer.database.repos.operation_decorator import (
    extract_error_details,
    get_operation_name,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


@pytest.mark.parametrize(
    "func,args,expected_repo,expected_op",
    [
        pytest.param(
            lambda x: None,
            (Mock(__class__=Mock(__name__="TestRepo")),),
            "TestRepo",
            "<lambda>",
            id="Mock Repo",
        ),
        pytest.param(lambda: None, tuple(), None, "<lambda>", id="None"),
        pytest.param(
            lambda x: None, ("string-arg",), None, "<lambda>", id="Not a Class"
        ),
    ],
)
def test_get_operation_name(func, args, expected_repo, expected_op):
    """
    Ensure that we can get the name of the operation correctly
    """
    repo_name, op_name = get_operation_name(func, args)
    assert repo_name == expected_repo
    assert op_name == expected_op


@pytest.mark.parametrize(
    "exception,expected_msg,expected_details",
    [
        pytest.param(
            IntegrityError(
                statement="INSERT INTO test",
                params={"id": 1},
                orig=Exception("duplicate key"),
            ),
            "duplicate key",
            {"sql_statement": "INSERT INTO test", "sql_params": "{'id': 1}"},
            id="integrity-error",
        ),
        pytest.param(
            ValueError("simple error"), "simple error", {}, id="Standard Error"
        ),
        pytest.param(
            SQLAlchemyError("multi\nline\nerror"),
            "multi",
            {"sql_statement": "", "sql_params": "{}"},
            id="Multiline Error",
        ),
    ],
)
def test_extract_error_details(exception, expected_msg, expected_details):
    """
    Test extracting the sql stqatement and params
    """
    msg, details = extract_error_details(exception)
    assert expected_msg in msg
    assert details == expected_details
