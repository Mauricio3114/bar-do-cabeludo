from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from app import db
from app.models.usuario import Usuario


usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


# =========================================================
# PROTEÇÃO ADMIN
# =========================================================

def somente_admin():

    if current_user.perfil != "admin":

        flash(
            "Acesso permitido somente para administrador.",
            "danger"
        )

        return False

    return True


# =========================================================
# LISTAGEM
# =========================================================

@usuarios_bp.route("/")
@login_required
def listar():

    if not somente_admin():
        return redirect(url_for("index"))

    usuarios = (
        Usuario.query
        .order_by(
            Usuario.ativo.desc(),
            Usuario.nome.asc()
        )
        .all()
    )

    return render_template(
        "usuarios/listar.html",
        usuarios=usuarios
    )


# =========================================================
# NOVO USUÁRIO
# =========================================================

@usuarios_bp.route(
    "/novo",
    methods=["GET", "POST"]
)
@login_required
def novo():

    if not somente_admin():
        return redirect(url_for("index"))

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        usuario_login = request.form.get(
            "usuario",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        perfil = request.form.get(
            "perfil",
            "garcom"
        )

        if not nome:
            flash(
                "Informe o nome.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=None
            )

        if not usuario_login:
            flash(
                "Informe o usuário de acesso.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=None
            )

        if not senha:
            flash(
                "Informe uma senha.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=None
            )

        if perfil not in [
            "admin",
            "garcom"
        ]:

            perfil = "garcom"

        existe = Usuario.query.filter_by(
            usuario=usuario_login
        ).first()

        if existe:

            flash(
                "Este usuário de acesso já existe.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=None
            )

        novo_usuario = Usuario(
            nome=nome,
            usuario=usuario_login,
            perfil=perfil,
            ativo=True
        )

        novo_usuario.set_senha(
            senha
        )

        db.session.add(
            novo_usuario
        )

        db.session.commit()

        flash(
            "Usuário cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("usuarios.listar")
        )

    return render_template(
        "usuarios/form.html",
        usuario=None
    )


# =========================================================
# EDITAR
# =========================================================

@usuarios_bp.route(
    "/<int:usuario_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar(usuario_id):

    if not somente_admin():
        return redirect(url_for("index"))

    usuario = db.session.get(
        Usuario,
        usuario_id
    )

    if not usuario:

        flash(
            "Usuário não encontrado.",
            "danger"
        )

        return redirect(
            url_for("usuarios.listar")
        )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        usuario_login = request.form.get(
            "usuario",
            ""
        ).strip().lower()

        perfil = request.form.get(
            "perfil",
            "garcom"
        )

        nova_senha = request.form.get(
            "senha",
            ""
        )

        if not nome or not usuario_login:

            flash(
                "Nome e usuário são obrigatórios.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=usuario
            )

        duplicado = (
            Usuario.query
            .filter(
                Usuario.usuario == usuario_login,
                Usuario.id != usuario.id
            )
            .first()
        )

        if duplicado:

            flash(
                "Este usuário de acesso já está sendo utilizado.",
                "danger"
            )

            return render_template(
                "usuarios/form.html",
                usuario=usuario
            )

        if perfil not in [
            "admin",
            "garcom"
        ]:

            perfil = "garcom"

        usuario.nome = nome
        usuario.usuario = usuario_login
        usuario.perfil = perfil

        if nova_senha:
            usuario.set_senha(
                nova_senha
            )

        db.session.commit()

        flash(
            "Usuário atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("usuarios.listar")
        )

    return render_template(
        "usuarios/form.html",
        usuario=usuario
    )


# =========================================================
# ATIVAR / DESATIVAR
# =========================================================

@usuarios_bp.route(
    "/<int:usuario_id>/status",
    methods=["POST"]
)
@login_required
def alterar_status(usuario_id):

    if not somente_admin():
        return redirect(url_for("index"))

    usuario = db.session.get(
        Usuario,
        usuario_id
    )

    if not usuario:

        flash(
            "Usuário não encontrado.",
            "danger"
        )

        return redirect(
            url_for("usuarios.listar")
        )

    # Não deixa o administrador
    # desativar a própria conta.
    if usuario.id == current_user.id:

        flash(
            "Você não pode desativar seu próprio usuário.",
            "danger"
        )

        return redirect(
            url_for("usuarios.listar")
        )

    usuario.ativo = not usuario.ativo

    db.session.commit()

    if usuario.ativo:

        flash(
            "Usuário ativado.",
            "success"
        )

    else:

        flash(
            "Usuário desativado.",
            "success"
        )

    return redirect(
        url_for("usuarios.listar")
    )