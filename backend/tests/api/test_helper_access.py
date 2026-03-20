from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.helper_access import validate_user_path_access


@pytest.mark.asyncio
async def test_validate_user_path_access_rejects_invalid_uuid() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await validate_user_path_access(
            user_id=uuid4(),
            path="/ludus/opus/not-a-uuid",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid item ID in path"


@pytest.mark.asyncio
async def test_validate_user_path_access_allows_own_user_path() -> None:
    user_id = uuid4()

    assert await validate_user_path_access(
        user_id=user_id,
        path=f"/ludus/user/{user_id}",
    ) is None
