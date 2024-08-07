import enum

from sqlmodel import Relationship

from app.sqlmodel.models.base import AppBase, ReadBase, TableBase
from app.sqlmodel.models.user import User, UserRead
from app.sqlmodel.models.userTodo import UserTodo


class TodoPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TodoBase(AppBase):
    title: str
    description: str | None
    priority: TodoPriority


class Todo(TodoBase, TableBase, table=True):
    users: list["User"] = Relationship(
        back_populates="todos", link_model=UserTodo, sa_relationship_kwargs={"lazy": "selectin"}
    )


class TodoRead(ReadBase, TodoBase):
    id: int


class TodoReadUsers(AppBase):
    id: int
    users: list["UserRead"] = []


class TodoCreate(TodoBase):
    users_id: list[int] | None


class TodoUpdate(TodoBase):
    users_id: list[int] | None
