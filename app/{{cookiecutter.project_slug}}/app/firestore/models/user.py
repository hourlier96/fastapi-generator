from datetime import datetime

from app.models.base import DateTimeModelMixin


class UserBase(DateTimeModelMixin[datetime]):
    """User Model"""

    first_name: str
    last_name: str
    email: str


class UserRead(UserBase):
    id: str


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass
