from typing import Any, List, Optional

from fastapi import APIRouter, Depends

from app.api.deps import raise_400, raise_404, raise_500
from app.core.cloud_logging import log
from app.models.base import Page
from app.sqlmodel.api.deps import parse_query_filter_params, session_dep
from app.sqlmodel.crud.todo import todos as crud_todo
from app.sqlmodel.models.base import QueryFilter
from app.sqlmodel.models.todo import (
    Todo,
    TodoCreate,
    TodoRead,
    TodoReadUsers,
    TodoUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=Page[TodoRead],
)
async def read_todos(
    *,
    db: session_dep,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20,
    sort: Optional[str] = None,
    filters: List[QueryFilter] = Depends(parse_query_filter_params),
    is_desc: bool = False,
    use_or: bool = False,
) -> Page[Todo]:
    """
    Retrieve crud_todo.
    """
    try:
        todos = await crud_todo.get_multi(
            db,
            page=page,
            per_page=per_page,
            sort=sort,
            is_desc=is_desc,
            filters=filters,
            use_or=use_or,
        )
        return todos
    except (AttributeError, KeyError, ValueError) as e:
        log.exception(e)
        raise_400()
    except Exception as e:
        log.exception(e)
        raise_500()


@router.get(
    "/withusers",
    response_model=List[TodoReadUsers],
)
async def read_todos_users(
    *,
    db: session_dep,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20,
    sort: Optional[str] = None,
    filters: List[QueryFilter] = Depends(parse_query_filter_params),
    is_desc: bool = False,
    use_or: bool = False,
) -> List[Todo]:
    """
    Retrieve todos sorted by users.
    """
    try:
        todos = await crud_todo.get_multi(
            db,
            page=page,
            per_page=per_page,
            sort=sort,
            is_desc=is_desc,
            filters=filters,
            use_or=use_or,
        )
        return todos.items
    except Exception as e:
        log.exception(e)
        raise_500()


@router.post(
    "",
    response_model=TodoRead,
)
async def create_todo(
    *,
    db: session_dep,
    todo_in: TodoCreate,
) -> Any:
    """
    Create a todo.
    """
    try:
        todo = await crud_todo.create(db=db, obj_in=todo_in)
        await crud_todo.update_users(db=db, todo_in=todo_in, todo=todo)
        await db.commit()
        await db.refresh(todo)
    except Exception as e:
        await db.rollback()
        log.exception(e)
        raise_500()

    return todo


@router.put(
    "/{_id}",
    response_model=TodoRead,
)
async def update_todo(
    *,
    db: session_dep,
    _id: int,
    todo_in: TodoUpdate,
) -> Any:
    """
    Update a todo.
    """
    todo = await crud_todo.get(db=db, id=_id)
    if not todo:
        raise_404()
    try:
        todo = await crud_todo.update(db=db, db_obj=todo, obj_in=todo_in)
        await crud_todo.update_users(db=db, todo_in=todo_in, todo=todo)
        await db.commit()
        await db.refresh(todo)
    except Exception as e:
        log.exception(e)
        raise_500()

    return todo


@router.get(
    "/{_id}",
    response_model=TodoRead,
)
async def read_todo(
    *,
    db: session_dep,
    _id: int,
) -> Any:
    """
    Get todo by ID.
    """
    todo = await crud_todo.get(db=db, id=_id)
    if not todo:
        raise_404()

    return todo


@router.get(
    "/{_id}/users/",
    response_model=TodoReadUsers,
)
async def read_todo_users(
    *,
    db: session_dep,
    _id: int,
) -> Todo:
    """
    Get user linked to a todo by todo ID.
    """
    todo = await crud_todo.get(db=db, id=_id)
    if not todo:
        raise_404()

    return todo


@router.delete(
    "/{_id}",
    response_model=TodoRead,
)
async def delete_todo(
    *,
    db: session_dep,
    _id: int,
) -> Any:
    """
    Delete a todo.
    """
    todo = await crud_todo.get(db=db, id=_id)
    if not todo:
        raise_404()

    try:
        todo = await crud_todo.remove(db=db, db_obj=todo)
    except Exception as e:
        log.exception(e)
        raise_500()

    return todo
