"""Adiciona carnes escolhidas no misto

Revision ID: d260e7cf9d39
Revises: a484ce20655b
Create Date: 2026-08-14 10:21:58.175153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd260e7cf9d39'
down_revision = 'a484ce20655b'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table(
        "itens_pedido",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "carne_escolha_1_id",
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                "carne_escolha_2_id",
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_foreign_key(
            "fk_itens_pedido_carne_escolha_1_produtos",
            "produtos",
            ["carne_escolha_1_id"],
            ["id"]
        )

        batch_op.create_foreign_key(
            "fk_itens_pedido_carne_escolha_2_produtos",
            "produtos",
            ["carne_escolha_2_id"],
            ["id"]
        )


def downgrade():

    with op.batch_alter_table(
        "itens_pedido",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_itens_pedido_carne_escolha_2_produtos",
            type_="foreignkey"
        )

        batch_op.drop_constraint(
            "fk_itens_pedido_carne_escolha_1_produtos",
            type_="foreignkey"
        )

        batch_op.drop_column(
            "carne_escolha_2_id"
        )

        batch_op.drop_column(
            "carne_escolha_1_id"
        )
