from datetime import datetime
from decimal import Decimal

from app import db


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    # =====================================================
    # TIPO
    # =====================================================

    tipo = db.Column(
        db.String(30),
        nullable=False
    )
    # carne
    # acompanhamento
    # bebida
    # sobremesa
    # outro

    # =====================================================
    # PREÇOS
    # =====================================================

    # Preço normal do produto.
    # Exemplo:
    # prato de picanha = 28.00
    # refrigerante = 6.00
    # acompanhamento incluído = 0.00
    preco = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    # =====================================================
    # ADICIONAL
    # =====================================================

    permite_adicional = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    preco_adicional = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    unidade_adicional = db.Column(
        db.String(30),
        nullable=True
    )
    # fatia
    # unidade
    # porcao
    # outro

    # =====================================================
    # OPERAÇÃO
    # =====================================================

    # =====================================================
    # DESTINO DO PREPARO
    # =====================================================

    destino_preparo = db.Column(
        db.String(30),
        nullable=False,
        default="sem_preparo"
    )
    # churrasqueira
    # cozinha
    # sem_preparo

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    ordem = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =====================================================
    # RELACIONAMENTO
    # =====================================================

    categoria = db.relationship(
        "Categoria",
        back_populates="produtos"
    )

    def __repr__(self):
        return f"<Produto {self.nome}>"