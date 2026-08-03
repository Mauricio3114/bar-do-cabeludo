from datetime import datetime
from decimal import Decimal

from app import db


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)

    # =====================================================
    # TIPO DE ATENDIMENTO
    # =====================================================

    tipo_atendimento = db.Column(
        db.String(20),
        nullable=False,
        default="mesa"
    )
    # mesa
    # marmitex

    mesa_id = db.Column(
        db.Integer,
        db.ForeignKey("mesas.id"),
        nullable=True,
        index=True
    )

    numero_marmitex = db.Column(
        db.Integer,
        nullable=True
    )

    # =====================================================
    # GARÇOM
    # =====================================================

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    # =====================================================
    # STATUS OPERACIONAL
    # =====================================================

    status = db.Column(
        db.String(30),
        nullable=False,
        default="aberto",
        index=True
    )

    # aberto
    # churrasqueira
    # cozinha
    # servido
    # fechamento
    # finalizado
    # cancelado

    # =====================================================
    # VALORES
    # =====================================================

    subtotal = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    desconto = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    # =====================================================
    # HORÁRIOS
    # =====================================================

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    enviado_churrasqueira_em = db.Column(
        db.DateTime,
        nullable=True
    )

    enviado_cozinha_em = db.Column(
        db.DateTime,
        nullable=True
    )

    servido_em = db.Column(
        db.DateTime,
        nullable=True
    )

    finalizado_em = db.Column(
        db.DateTime,
        nullable=True
    )

    # =====================================================
    # RELACIONAMENTOS
    # =====================================================

    mesa = db.relationship(
        "Mesa",
        backref="pedidos"
    )

    usuario = db.relationship(
        "Usuario",
        backref="pedidos"
    )

    itens = db.relationship(
        "ItemPedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
        lazy=True
    )

    # =====================================================
    # FECHAMENTO / PAGAMENTO
    # =====================================================

    forma_pagamento = db.Column(
        db.String(30),
        nullable=True
    )

    fechamento_em = db.Column(
        db.DateTime,
        nullable=True
    )

    def __repr__(self):
        return f"<Pedido {self.id}>"