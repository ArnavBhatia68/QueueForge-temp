from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e161f3005cc9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


job_status_enum = postgresql.ENUM(
    'QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'RETRYING', 'CANCELLED',
    name='jobstatus'
)

job_status_enum_ref = postgresql.ENUM(
    'QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'RETRYING', 'CANCELLED',
    name='jobstatus',
    create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    job_status_enum.create(bind, checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'queues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
    )
    op.create_index('ix_queues_id', 'queues', ['id'], unique=False)
    op.create_index('ix_queues_name', 'queues', ['name'], unique=True)

    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('queue_name', sa.String(), sa.ForeignKey('queues.name'), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('status', job_status_enum_ref, nullable=True, server_default='QUEUED'),
        sa.Column('attempts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('worker_id', sa.String(), nullable=True),
    )
    op.create_index('ix_jobs_id', 'jobs', ['id'], unique=False)
    op.create_index('ix_jobs_owner_id', 'jobs', ['owner_id'], unique=False)
    op.create_index('ix_jobs_queue_name', 'jobs', ['queue_name'], unique=False)
    op.create_index('ix_jobs_type', 'jobs', ['type'], unique=False)
    op.create_index('ix_jobs_priority', 'jobs', ['priority'], unique=False)
    op.create_index('ix_jobs_status', 'jobs', ['status'], unique=False)

    op.create_table(
        'job_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('level', sa.String(), nullable=True, server_default='INFO'),
    )
    op.create_index('ix_job_logs_id', 'job_logs', ['id'], unique=False)
    op.create_index('ix_job_logs_job_id', 'job_logs', ['job_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_logs_job_id', table_name='job_logs')
    op.drop_index('ix_job_logs_id', table_name='job_logs')
    op.drop_table('job_logs')

    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_priority', table_name='jobs')
    op.drop_index('ix_jobs_type', table_name='jobs')
    op.drop_index('ix_jobs_queue_name', table_name='jobs')
    op.drop_index('ix_jobs_owner_id', table_name='jobs')
    op.drop_index('ix_jobs_id', table_name='jobs')
    op.drop_table('jobs')

    op.drop_index('ix_queues_name', table_name='queues')
    op.drop_index('ix_queues_id', table_name='queues')
    op.drop_table('queues')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')

    job_status_enum.drop(op.get_bind(), checkfirst=True)
