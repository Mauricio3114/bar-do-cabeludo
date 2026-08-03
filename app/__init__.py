from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):

    from app.models.usuario import Usuario

    return db.session.get(
        Usuario,
        int(user_id)
    )


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    # =====================================================
    # EXTENSÕES
    # =====================================================

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    login_manager.login_message = (
        "Faça login para continuar."
    )

    login_manager.login_message_category = "warning"


    # =====================================================
    # MODELS
    # =====================================================

    from app.models.usuario import Usuario
    from app.models.mesa import Mesa
    from app.models.categoria import Categoria
    from app.models.produto import Produto
    from app.models.pedido import Pedido
    from app.models.item_pedido import ItemPedido
    from app.models.item_pedido_acompanhamento import ItemPedidoAcompanhamento


    # =====================================================
    # BLUEPRINTS
    # =====================================================

    from app.routes.auth import auth_bp
    from app.routes.mesas import mesas_bp
    from app.routes.produtos import produtos_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.painel import painel_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.caixa import caixa_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(mesas_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(painel_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(caixa_bp)


    # =====================================================
    # ENTRADA TEMPORÁRIA DO SISTEMA
    # =====================================================

    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("mesas.listar"))

    return app