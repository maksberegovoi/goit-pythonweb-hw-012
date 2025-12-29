"""Add user role

Revision ID: c3f039ae1897
Revises: c129e31e22e8
Create Date: 2025-12-26 05:12:53.357118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f039ae1897'
down_revision: Union[str, Sequence[str], None] = 'c129e31e22e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    userrole_enum = sa.Enum('ADMIN', 'USER', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'users',
        sa.Column('role', userrole_enum, nullable=False, server_default='USER')
    )

def downgrade() -> None:
    op.drop_column('users', 'role')
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
