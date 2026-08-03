from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import login_required, current_user

from app import db
from app.models.categoria import Categoria
from app.models.produto import Produto


produtos_bp = Blueprint(
    "produtos",
    __name__,
    url_prefix="/produtos"
)


# =========================================================
# AUXILIAR
# =========================================================

def somente_admin():
    return current_user.perfil == "admin"


def converter_decimal(valor):
    """
    Aceita:
    28
    28.00
    28,00
    1.250,50
    """

    if valor is None:
        return Decimal("0.00")

    valor = str(valor).strip()

    if not valor:
        return Decimal("0.00")

    if "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    try:
        return Decimal(valor)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


# =========================================================
# LISTAGEM
# =========================================================

@produtos_bp.route("/")
@login_required
def listar():

    if not somente_admin():
        flash(
            "Acesso permitido somente ao administrador.",
            "danger"
        )
        return redirect(url_for("mesas.listar"))

    categorias = (
        Categoria.query
        .order_by(Categoria.ordem.asc(), Categoria.nome.asc())
        .all()
    )

    produtos = (
        Produto.query
        .join(Categoria)
        .order_by(
            Categoria.ordem.asc(),
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    total = len(produtos)

    ativos = sum(
        1 for produto in produtos
        if produto.ativo
    )

    adicionais = sum(
        1 for produto in produtos
        if produto.permite_adicional and produto.ativo
    )

    return render_template(
        "produtos/listar.html",
        produtos=produtos,
        categorias=categorias,
        total=total,
        ativos=ativos,
        adicionais=adicionais
    )


# =========================================================
# NOVO
# =========================================================

@produtos_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():

    if not somente_admin():
        flash(
            "Acesso permitido somente ao administrador.",
            "danger"
        )
        return redirect(url_for("mesas.listar"))

    categorias = (
        Categoria.query
        .filter_by(ativa=True)
        .order_by(Categoria.ordem.asc(), Categoria.nome.asc())
        .all()
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        categoria_id = request.form.get(
            "categoria_id",
            type=int
        )

        tipo = request.form.get(
            "tipo",
            ""
        ).strip()

        preco = converter_decimal(
            request.form.get("preco")
        )

        permite_adicional = (
            request.form.get("permite_adicional")
            == "on"
        )

        preco_adicional = converter_decimal(
            request.form.get("preco_adicional")
        )

        unidade_adicional = request.form.get(
            "unidade_adicional",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            0,
            type=int
        )

        # ---------------------------------------------
        # VALIDAÇÕES
        # ---------------------------------------------

        if not nome:
            flash(
                "Informe o nome do produto.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=None
            )

        categoria = db.session.get(
            Categoria,
            categoria_id
        )

        if not categoria:
            flash(
                "Selecione uma categoria válida.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=None
            )

        tipos_validos = {
            "carne",
            "acompanhamento",
            "bebida",
            "sobremesa",
            "outro"
        }

        if tipo not in tipos_validos:
            flash(
                "Selecione o tipo do produto.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=None
            )

        if permite_adicional and preco_adicional < 0:
            flash(
                "O preço do adicional é inválido.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=None
            )

        # ---------------------------------------------
        # SALVAR
        # ---------------------------------------------

        produto = Produto(
            categoria_id=categoria.id,
            nome=nome,
            tipo=tipo,
            preco=preco,
            permite_adicional=permite_adicional,
            preco_adicional=(
                preco_adicional
                if permite_adicional
                else Decimal("0.00")
            ),
            unidade_adicional=(
                unidade_adicional
                if permite_adicional
                else None
            ),
            ordem=ordem,
            ativo=True
        )

        db.session.add(produto)
        db.session.commit()

        flash(
            "Produto cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produtos.listar")
        )

    return render_template(
        "produtos/form.html",
        categorias=categorias,
        produto=None
    )


# =========================================================
# EDITAR
# =========================================================

@produtos_bp.route(
    "/<int:produto_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar(produto_id):

    if not somente_admin():
        flash(
            "Acesso permitido somente ao administrador.",
            "danger"
        )
        return redirect(url_for("mesas.listar"))

    produto = Produto.query.get_or_404(
        produto_id
    )

    categorias = (
        Categoria.query
        .filter_by(ativa=True)
        .order_by(Categoria.ordem.asc(), Categoria.nome.asc())
        .all()
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        categoria_id = request.form.get(
            "categoria_id",
            type=int
        )

        tipo = request.form.get(
            "tipo",
            ""
        ).strip()

        preco = converter_decimal(
            request.form.get("preco")
        )

        permite_adicional = (
            request.form.get("permite_adicional")
            == "on"
        )

        preco_adicional = converter_decimal(
            request.form.get("preco_adicional")
        )

        unidade_adicional = request.form.get(
            "unidade_adicional",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            0,
            type=int
        )

        if not nome:
            flash(
                "Informe o nome do produto.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=produto
            )

        categoria = db.session.get(
            Categoria,
            categoria_id
        )

        if not categoria:
            flash(
                "Selecione uma categoria válida.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=produto
            )

        tipos_validos = {
            "carne",
            "acompanhamento",
            "bebida",
            "sobremesa",
            "outro"
        }

        if tipo not in tipos_validos:
            flash(
                "Selecione o tipo do produto.",
                "danger"
            )
            return render_template(
                "produtos/form.html",
                categorias=categorias,
                produto=produto
            )

        produto.nome = nome
        produto.categoria_id = categoria.id
        produto.tipo = tipo
        produto.preco = preco
        produto.permite_adicional = permite_adicional

        produto.preco_adicional = (
            preco_adicional
            if permite_adicional
            else Decimal("0.00")
        )

        produto.unidade_adicional = (
            unidade_adicional
            if permite_adicional
            else None
        )

        produto.ordem = ordem

        db.session.commit()

        flash(
            "Produto atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("produtos.listar")
        )

    return render_template(
        "produtos/form.html",
        categorias=categorias,
        produto=produto
    )


# =========================================================
# ATIVAR / INATIVAR
# =========================================================

@produtos_bp.route(
    "/<int:produto_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status(produto_id):

    if not somente_admin():
        flash(
            "Acesso permitido somente ao administrador.",
            "danger"
        )
        return redirect(url_for("mesas.listar"))

    produto = Produto.query.get_or_404(
        produto_id
    )

    produto.ativo = not produto.ativo

    db.session.commit()

    if produto.ativo:
        flash(
            f"{produto.nome} ativado.",
            "success"
        )
    else:
        flash(
            f"{produto.nome} desativado.",
            "success"
        )

    return redirect(
        url_for("produtos.listar")
    )