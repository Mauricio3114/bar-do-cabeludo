from flask import Blueprint, render_template
from flask_login import login_required

from app.models.mesa import Mesa


mesas_bp = Blueprint(
    "mesas",
    __name__,
    url_prefix="/mesas"
)


@mesas_bp.route("/")
@login_required
def listar():

    mesas = (
        Mesa.query
        .filter_by(ativa=True)
        .order_by(Mesa.numero.asc())
        .all()
    )

    return render_template(
        "mesas/listar.html",
        mesas=mesas
    )