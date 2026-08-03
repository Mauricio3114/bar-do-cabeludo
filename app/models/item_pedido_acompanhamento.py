from app import db


class ItemPedidoAcompanhamento(db.Model):
    __tablename__ = "itens_pedido_acompanhamentos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    item_pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("itens_pedido.id"),
        nullable=False,
        index=True
    )

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=False,
        index=True
    )

    item_pedido = db.relationship(
        "ItemPedido",
        back_populates="acompanhamentos"
    )

    produto = db.relationship(
        "Produto"
    )

    def __repr__(self):
        return (
            f"<ItemPedidoAcompanhamento "
            f"{self.id}>"
        )