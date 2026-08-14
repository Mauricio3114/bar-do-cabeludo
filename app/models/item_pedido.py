from decimal import Decimal

from app import db


class ItemPedido(db.Model):
    __tablename__ = "itens_pedido"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id"),
        nullable=False,
        index=True
    )

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=False,
        index=True
    )

    # normal
    # adicional
    tipo_item = db.Column(
        db.String(20),
        nullable=False,
        default="normal"
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    valor_unitario = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    valor_total = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    observacao = db.Column(
        db.String(255),
        nullable=True
    )

    # =====================================================
    # CONTROLE DE FLUXO DO PRATO
    # =====================================================

    status_preparo = db.Column(
        db.String(30),
        nullable=True,
        index=True
    )
    # None = item segue o fluxo global/original da comanda
    # churrasqueira = prato adicionado depois, aguardando carne
    # cozinha = carne pronta, aguardando acompanhamentos
    # servido = prato adicional já entregue

    # =====================================================
    # CARNES ESCOLHIDAS NO PRATO MISTO
    # =====================================================

    carne_escolha_1_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=True
    )

    carne_escolha_2_id = db.Column(
        db.Integer,
        db.ForeignKey("produtos.id"),
        nullable=True
    )

    # =====================================================
    # RELACIONAMENTOS
    # =====================================================

    pedido = db.relationship(
        "Pedido",
        back_populates="itens"
    )

    produto = db.relationship(
        "Produto",
        foreign_keys=[produto_id]
    )

    acompanhamentos = db.relationship(
        "ItemPedidoAcompanhamento",
        back_populates="item_pedido",
        cascade="all, delete-orphan",
        lazy=True
    )

    carne_escolha_1 = db.relationship(
        "Produto",
        foreign_keys=[carne_escolha_1_id]
    )

    carne_escolha_2 = db.relationship(
        "Produto",
        foreign_keys=[carne_escolha_2_id]
    )

    def __repr__(self):
        return f"<ItemPedido {self.id}>"