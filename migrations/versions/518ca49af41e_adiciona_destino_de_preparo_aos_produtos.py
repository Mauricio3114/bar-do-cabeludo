"""Adiciona destino de preparo aos produtos

Revision ID: 518ca49af41e
Revises: 55646a4ba323
Create Date: 2026-08-03 09:14:24.817656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '518ca49af41e'
down_revision = '55646a4ba323'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'destino_preparo',
                sa.String(length=30),
                nullable=False,
                server_default='sem_preparo'
            )
        )


def downgrade():
    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.drop_column('destino_preparo')