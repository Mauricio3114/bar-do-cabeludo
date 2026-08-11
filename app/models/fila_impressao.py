from datetime import datetime

from app import db


class FilaImpressao(db.Model):
    __tablename__ = "fila_impressoes"

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

    destino = db.Column(
        db.String(30),
        nullable=False,
        index=True
    )
    # churrasqueira
    # cozinha

    tipo = db.Column(
        db.String(30),
        nullable=False,
        default="pedido"
    )
    # pedido
    # novo_consumo

    item_ids = db.Column(
        db.Text,
        nullable=True
    )
    # IDs separados por vírgula quando for novo consumo

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pendente",
        index=True
    )
    # pendente
    # processando
    # impresso
    # erro

    tentativas = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    erro = db.Column(
        db.Text,
        nullable=True
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    processado_em = db.Column(
        db.DateTime,
        nullable=True
    )

    pedido = db.relationship(
        "Pedido",
        backref="fila_impressoes"
    )

    def __repr__(self):
        return (
            f"<FilaImpressao "
            f"{self.id} "
            f"{self.destino} "
            f"{self.status}>"
        )