"""add project and task planning fields

Revision ID: 9f4b2c7d1a3e
Revises: 3a7000b81a4f
Create Date: 2026-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f4b2c7d1a3e'
down_revision = '3a7000b81a4f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.add_column(
            sa.Column(
                'priority',
                sa.String(length=10),
                nullable=False,
                server_default='medium',
            )
        )
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.drop_constraint('ck_tasks_status', type_='check')
        batch_op.create_check_constraint(
            'ck_tasks_status',
            "status IN ('pending', 'in_progress', 'completed')",
        )
        batch_op.create_check_constraint(
            'ck_tasks_priority', "priority IN ('low', 'medium', 'high')"
        )

    # Preserve a useful completion date for tasks completed before this migration.
    op.execute(
        "UPDATE tasks SET completed_at = updated_at "
        "WHERE status = 'completed' AND completed_at IS NULL"
    )


def downgrade():
    op.execute(
        "UPDATE tasks SET status = 'pending' "
        "WHERE status NOT IN ('pending', 'completed')"
    )

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_constraint('ck_tasks_priority', type_='check')
        batch_op.drop_constraint('ck_tasks_status', type_='check')
        batch_op.create_check_constraint(
            'ck_tasks_status', "status IN ('pending', 'completed')"
        )
        batch_op.drop_column('completed_at')
        batch_op.drop_column('due_date')
        batch_op.drop_column('priority')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('due_date')
