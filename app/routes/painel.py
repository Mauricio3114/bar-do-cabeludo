from datetime import timedelta

from flask import Blueprint, render_template

from app.models.pedido import Pedido


painel_bp = Blueprint(
    "painel",
    __name__,
    url_prefix="/painel"
)


@painel_bp.route("/")
def tv():

    pedidos = (
        Pedido.query
        .filter(
            Pedido.status.in_([
                "churrasqueira",
                "cozinha",
                "servido",
                "fechamento"
            ])
        )
        .order_by(
            Pedido.criado_em.asc()
        )
        .all()
    )

    return render_template(
        "painel/tv.html",
        pedidos=pedidos,
        timedelta=timedelta
    )