from datetime import datetime

from app import db


class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)

    numero = db.Column(
        db.Integer,
        unique=True,
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(50),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="livre"
    )
    # livre
    # churrasqueira
    # cozinha
    # servido
    # fechamento

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

    def __repr__(self):
        return f"<Mesa {self.numero:02d}>"