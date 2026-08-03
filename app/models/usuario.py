from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    usuario = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    senha_hash = db.Column(
        db.String(255),
        nullable=False
    )

    perfil = db.Column(
        db.String(20),
        nullable=False,
        default="garcom"
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.nome}>"