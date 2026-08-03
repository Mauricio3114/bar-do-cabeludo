from datetime import datetime

from app import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(80),
        nullable=False,
        unique=True
    )

    ordem = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    ativa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    criada_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    produtos = db.relationship(
        "Produto",
        back_populates="categoria",
        lazy=True
    )

    def __repr__(self):
        return f"<Categoria {self.nome}>"