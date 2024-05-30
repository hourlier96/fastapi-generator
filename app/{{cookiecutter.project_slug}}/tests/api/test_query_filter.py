from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from tests.utils.query_filter import call_from_operator
from tests.utils.user import create_user

DATASOURCES_URL = f"{settings.API_PREFIX}/user"


async def test_query_filter_users(client: AsyncClient, db: AsyncSession) -> None:
    user0 = await create_user(
        db, "Jean", "jean.dupont@gmail.com", "jean.dupont@gmail.com", True, 135
    )
    await create_user(db, "Louis", "Ferrand", "louis.ferrand@gmail.com", False, 10)
    await create_user(db, "Anna", "", "anna.delcourt@gmail.com", False, None)

    query_params = {
        "page": 1,
        "per_page": 20,
        "sort": None,
        "is_desc": False,
        "filters": None,
    }
    # Test equality operators
    data = await call_from_operator(client, query_params, "first_name", "eq", user0.first_name)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "first_name", "=", user0.first_name)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "email", "!=", user0.email)
    assert data.get("total") > 1
    data = await call_from_operator(client, query_params, "email", "ne", user0.email)
    assert data.get("total") > 1
    data = await call_from_operator(client, query_params, "email", "neq", user0.email)
    assert data.get("total") > 1
    # Test inclusion operators
    data = await call_from_operator(client, query_params, "email", ":", "%dupont%")
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "email", "has", "%dupont%")
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "email", "contains", "%dupont%")
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "email", "includes", "%dupont%")
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "email", "like", "%dupont%")
    assert data.get("total") == 1
    # Test comparison operators
    data = await call_from_operator(client, query_params, "login_times", "<", 12)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "lt", 10)
    assert data.get("total") == 0
    data = await call_from_operator(client, query_params, "login_times", "<=", 10)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "le", 10)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", ">", 120)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "gt", 135)
    assert data.get("total") == 0
    data = await call_from_operator(client, query_params, "login_times", ">=", 135)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "ge", 135)
    assert data.get("total") == 1
    # Test range operators
    data = await call_from_operator(client, query_params, "login_times", "in", [1, 5, 10, 100])
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "not_in", [1, 2, 3])
    assert data.get("total") == 2
    # Test type operators
    data = await call_from_operator(client, query_params, "login_times", "is_null", None)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "login_times", "is_not_null", None)
    assert data.get("total") == 2
    data = await call_from_operator(client, query_params, "last_name", "is_empty", None)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "last_name", "is_not_empty", None)
    assert data.get("total") == 2
    data = await call_from_operator(client, query_params, "is_admin", "is_true", None)
    assert data.get("total") == 1
    data = await call_from_operator(client, query_params, "is_admin", "is_false", None)
    assert data.get("total") == 2

    # Test sort key
    query_params["sort"] = "first_name"
    data = await call_from_operator(client, query_params, "first_name", "is_not_empty", None)
    assert data.get("total") == 3
    items = data.get("items")
    assert items[0].get("first_name") == "Anna"
    assert items[1].get("first_name") == "Jean"
    assert items[2].get("first_name") == "Louis"
    # Test is_desc
    query_params["is_desc"] = True
    data = await call_from_operator(client, query_params, "first_name", "is_not_empty", None)
    assert data.get("total") == 3
    items = data.get("items")
    assert items[0].get("first_name") == "Louis"
    assert items[1].get("first_name") == "Jean"
    assert items[2].get("first_name") == "Anna"
