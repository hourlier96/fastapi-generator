"""user_with_todo

Revision ID: 1eb8ef4fc04e
Revises:
Create Date: 2024-02-02 15:03:08.732482

"""

from typing import Sequence, Union

import random
import sqlmodel
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import MetaData, Table
from faker import Faker

from app.sqlmodel.models.todo import TodoPriority


# revision identifiers, used by Alembic.
revision: str = "1eb8ef4fc04e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NB_TODO = 500
NB_USERS = 120


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "todo",
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("id", sa.Integer(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "priority", sa.Enum("LOW", "MEDIUM", "HIGH", name="todopriority"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("login_times", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "usertodo",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("todo_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["todo_id"],
            ["todo.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("todo_id", "user_id"),
    )

    fake = Faker()
    # get metadata from current connection
    meta = MetaData()
    # pass in tuple with tables we want to reflect, otherwise whole database will get reflected
    meta.reflect(
        bind=op.get_bind(),
        only=("todo", "user", "usertodo"),
    )
    todo_table = Table("todo", meta)
    op.bulk_insert(
        todo_table,
        [
            {
                "title": fake.sentence(nb_words=random.randint(3, 10)),
                "description": (
                    fake.paragraph(nb_sentences=random.randint(1, 6)) if fake.boolean() else None
                ),
                "priority": random.choice(list(TodoPriority)),
                "created_at": fake.date_time_this_month(),
                "updated_at": fake.date_time_this_month(),
            }
            for _ in range(NB_TODO)
        ],
    )
    user_table = Table("user", meta)
    op.bulk_insert(
        user_table,
        [
            {
                "first_name": fake.unique.first_name(),
                "last_name": (fake.unique.last_name()),
                "email": fake.unique.ascii_free_email(),
                "is_admin": fake.pybool(),
                "login_times": random.randint(0, 1000) if random.random() < 0.5 else None,
                "created_at": fake.date_time_this_month(),
                "updated_at": fake.date_time_this_month(),
            }
            for _ in range(NB_USERS)
        ],
    )
    usertodo_table = Table("usertodo", meta)
    associations = zip(
        random.sample(range(1, NB_USERS + 1), NB_USERS),
        random.sample(range(1, NB_TODO + 1), NB_TODO),
    )
    op.bulk_insert(
        usertodo_table,
        [
            {
                "user_id": association[0],
                "todo_id": association[1],
                "created_at": fake.date_time_this_month(),
                "updated_at": fake.date_time_this_month(),
            }
            for association in associations
        ],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("usertodo")
    op.drop_table("user")
    op.drop_table("todo")
    op.execute("DROP TYPE todopriority")
    # ### end Alembic commands ###
