from typing import Generic

from pydantic import BaseModel

from app.models.base import T, to_camel


class DateTimeModelMixin(BaseModel, Generic[T]):
    created_at: T
    updated_at: T

    class Config:
        alias_generator = to_camel
        populate_by_name = True
