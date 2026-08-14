"""Adiciona configuracao prato misto

Revision ID: a484ce20655b
Revises: 00047ff5a81a
Create Date: 2026-08-14 10:14:46.798008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a484ce20655b'
down_revision = '00047ff5a81a'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table(
        "produtos",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "permite_escolha_carnes",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        batch_op.add_column(
            sa.Column(
                "quantidade_carnes_escolha",
                sa.Integer(),
                nullable=False,
                server_default="0"
            )
        )


def downgrade():

    with op.batch_alter_table(
        "produtos",
        schema=None
    ) as batch_op:

        batch_op.drop_column(
            "quantidade_carnes_escolha"
        )

        batch_op.drop_column(
            "permite_escolha_carnes"
        )
