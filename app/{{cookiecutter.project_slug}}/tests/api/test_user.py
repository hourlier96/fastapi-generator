from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from tests.utils.user import build_random_user_in, create_random_user

DATASOURCES_URL = f"{settings.API_PREFIX}/user"


async def test_get_user(client: AsyncClient, db: AsyncSession) -> None:
    user = await create_random_user(db)
    response = await client.get(
        f"{DATASOURCES_URL}/{user.id}",
    )
    assert response.status_code == 200
    content = response.json()
    assert content.get("id") is not None


async def test_get_users(client: AsyncClient, db: AsyncSession) -> None:
    users = [
        await create_random_user(db),
        await create_random_user(db),
        await create_random_user(db),
    ]
    response = await client.get(
        f"{DATASOURCES_URL}",
    )
    assert response.status_code == 200

    content = response.json()
    assert content.get("total") == len(users)
    items = content.get("items")
    assert len(items) == len(users)


async def test_create_user(client: AsyncClient, db: AsyncSession) -> None:
    user = build_random_user_in()
    response = await client.post(
        DATASOURCES_URL,
        json=jsonable_encoder(user),
    )
    assert response.status_code == 200
    content = response.json()
    assert content.get("email") == user.email
