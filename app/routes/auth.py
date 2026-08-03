from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models.usuario import Usuario


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":

        usuario_digitado = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(
            usuario=usuario_digitado
        ).first()

        if not usuario or not usuario.verificar_senha(senha):
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("auth/login.html")

        if not usuario.ativo:
            flash("Este usuário está inativo.", "danger")
            return render_template("auth/login.html")

        login_user(usuario, remember=True)

        return redirect(url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("auth.login"))