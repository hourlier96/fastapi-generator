from sqlmodel import Field

from app.sqlmodel.models.base import AppBase, TableBase


class UserTodo(AppBase, TableBase, table=True):
    """Linking table between User and Todo"""

    todo_id: int | None = Field(
        default=None, foreign_key="todo.id", primary_key=True, nullable=False
    )
    user_id: int | None = Field(
        default=None, foreign_key="user.id", primary_key=True, nullable=False
    )
