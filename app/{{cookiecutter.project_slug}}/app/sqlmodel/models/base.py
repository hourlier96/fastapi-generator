import re
from datetime import UTC, date, datetime
from typing import Literal, TypeVar

from fastapi import HTTPException, status
from pydantic import model_validator
from sqlalchemy import TIMESTAMP, text
from sqlmodel import Field, SQLModel

from app.models.base import to_camel
from app.utils.date import formatAsDate

T = TypeVar("T")


def to_snake(camel_str: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()


def convert_datetime_to_realworld(dt: datetime) -> str:
    return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


class AppBase(SQLModel):
    class ConfigDict:
        alias_generator = to_camel
        populate_by_name = True
        json_encoders = {datetime: convert_datetime_to_realworld}


class ReadBase(SQLModel):
    id: int
    created_at: datetime
    updated_at: datetime


class TableBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True, nullable=False)

    created_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
        },
        default=datetime.now(),
        nullable=False,
    )

    updated_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
        default=datetime.now(),
        nullable=False,
    )


class QueryFilter(SQLModel):
    # fmt:off
    field: str
    operator: Literal[
        # comparison operators
        "<", "lt",
        "<=", "le",
        ">=", "ge",
        ">", "gt",
        ":", "has", "contains", "includes", "like",
        "=", "eq",
        "!=", "ne", "neq",
        # range operators
        "in",
        "not_in",
        # type operators
        "is_null",
        "is_not_null",
        "is_empty",
        "is_not_empty",
        "is_true",
        "is_false",
    ]
    value: int | date | datetime | str | list | None
    # fmt:on

    @model_validator(mode="before")
    def validate_value(cls, values: dict[str, str]) -> dict:
        # fmt:off
        comparison_operators: set[str] = {
            "<", "lt",
            "<=", "le",
            ">=", "ge",
            ">", "gt",
        }
        range_operators: set[str] = {
            "in",
            "not_in",
        }
        type_operators: set[str] = {
            "is_null",
            "is_not_null",
            "is_empty",
            "is_not_empty",
            "is_true",
            "is_false"
        }
        # fmt:on
        special_operators: set[str] = {*range_operators, *type_operators}

        field, operator, value = values["field"], values.get("operator"), values.get("value")
        values["field"] = to_snake(field)

        try:
            if isinstance(value, str):
                values["value"] = formatAsDate(value)
        except ValueError:
            pass

        if operator not in special_operators:
            if value is None:
                raise HTTPException(status_code=400, detail="Value is required for this operator.")

            if not isinstance(values["value"], int | float | date | datetime):
                if operator in comparison_operators:
                    raise ValueError(
                        f"Comparison operator requires type int, float, date or datetime: got {type(values['value'])}"
                    )

            if operator in ["eq", "="]:
                values["operator"] = "="
            elif operator in ["ne", "neq", "!="]:
                values["operator"] = "!="
            elif operator in ["has", "contains", "includes", "like", ":"]:
                values["operator"] = ":"
            elif operator in ["gt", ">"]:
                values["operator"] = ">"
            elif operator in ["ge", ">="]:
                values["operator"] = ">="
            elif operator in ["lt", "<"]:
                values["operator"] = "<"
            elif operator in ["le", "<="]:
                values["operator"] = "<="
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid operator",
                )

        else:
            if operator in range_operators:
                if not isinstance(value, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Value must be a list",
                    )
                if not value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Value cannot be empty",
                    )
            elif operator in type_operators:
                if value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Value must be empty",
                    )

        return values
