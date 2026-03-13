"""add queue ownership and job names

Revision ID: 4b6f8dd0ef3e
Revises: e161f3005cc9
Create Date: 2026-03-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4b6f8dd0ef3e'
down_revision: Union[str, None] = 'e161f3005cc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('queues', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_index('ix_queues_owner_id', 'queues', ['owner_id'], unique=False)
    op.create_foreign_key('fk_queues_owner_id_users', 'queues', 'users', ['owner_id'], ['id'])

    op.add_column('jobs', sa.Column('name', sa.String(), nullable=False, server_default='Untitled job'))


def downgrade() -> None:
    op.drop_column('jobs', 'name')

    op.drop_constraint('fk_queues_owner_id_users', 'queues', type_='foreignkey')
    op.drop_index('ix_queues_owner_id', table_name='queues')
    op.drop_column('queues', 'owner_id')
