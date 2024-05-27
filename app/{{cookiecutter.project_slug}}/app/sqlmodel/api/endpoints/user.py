from typing import Any, List, Optional

from fastapi import APIRouter, Depends

from app.api.deps import raise_404, raise_500
from app.core.cloud_logging import log
from app.models.base import Page
from app.sqlmodel.api.deps import parse_query_filter_params, session_dep
from app.sqlmodel.crud.user import users as crud_user
from app.sqlmodel.models.base import QueryFilter
from app.sqlmodel.models.user import User, UserCreate, UserRead

router = APIRouter()


@router.get(
    "",
    response_model=Page[UserRead],
)
async def read_users(
    *,
    db: session_dep,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20,
    sort: Optional[str] = None,
    filters: List[QueryFilter] = Depends(parse_query_filter_params),
    is_desc: bool = False,
    use_or: bool = False,
) -> Page[User]:
    """
    Retrieve user.
    """
    try:
        users = await crud_user.get_multi(
            db,
            page=page,
            per_page=per_page,
            sort=sort,
            is_desc=is_desc,
            filters=filters,
            use_or=use_or,
        )
        return users
    except Exception as e:
        log.exception(e)
        raise_500()


@router.post(
    "",
    response_model=UserRead,
)
async def create_user(
    *,
    db: session_dep,
    user_in: UserCreate,
) -> User:
    """
    Create new user.
    """
    try:
        user = await crud_user.create(db=db, obj_in=user_in)
    except Exception as e:
        log.exception(e)
        raise_500()

    return user


@router.get(
    "/{_id}",
    response_model=UserRead,
)
async def read_user(
    *,
    db: session_dep,
    _id: int,
) -> Any:
    """
    Get user by ID
    """
    user = await crud_user.get(db=db, id=_id)
    if not user:
        raise_404()

    return user
