from unittest.mock import AsyncMock

import pytest
from common_layer.database.repos.repo_naptan import NaptanStopPointRepo
from common_layer.dynamodb.client_loader import DynamoDBLoader

from periodic_tasks.naptan_cache_id_updater.app.process_updates import (
    process_private_code_updates,
)


@pytest.mark.asyncio
async def test_process_private_code_updates():
    """
    Test for processing private code updates
    """

    atco_code_id_map = {
        "atco1": 1,
        "atco2": 2,
        "atco3": 3,
    }

    m_repo = AsyncMock(spec=NaptanStopPointRepo)
    m_repo.stream_naptan_ids.return_value = iter([atco_code_id_map])

    # Mock DynamoDBLoader to return successful updates
    m_dynamo_loader = AsyncMock(spec=DynamoDBLoader)
    m_dynamo_loader.async_update_private_codes.return_value = (
        3,  # Success
        0,  # Failure
    )
    m_dynamo_loader.max_concurrent_batches = 5

    # Run the function
    processed, errors = await process_private_code_updates(m_dynamo_loader, m_repo)

    # Assertions
    assert processed == 3
    assert errors == 0
    m_repo.stream_naptan_ids.assert_called_once_with(batch_size=10000)
    m_dynamo_loader.async_update_private_codes.assert_called_once_with(atco_code_id_map)
