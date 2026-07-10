from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from config import Config
from flask_login import UserMixin

db = SQLAlchemy()

# Таблица связи "многие ко многим" для совладельцев
server_access = db.Table('server_access',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('server_id', db.Integer, db.ForeignKey('server.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    servers = db.relationship('Server', backref='owner', lazy=True)
    # Серверы, где пользователь является совладельцем
    co_servers = db.relationship('Server', secondary=server_access, backref=db.backref('co_owners', lazy='dynamic'))

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    server_type = db.Column(db.String(20), nullable=False, default='vanilla')
    mc_version = db.Column(db.String(20), nullable=False)
    ssh_host = db.Column(db.String(100), nullable=False)
    ssh_port = db.Column(db.Integer, default=22)
    ssh_user = db.Column(db.String(50), nullable=False)
    ssh_password_enc = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='offline')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Дополнительные поля
    startup_command = db.Column(db.Text, default="java -Xms128M -Xmx1024M -jar server.jar nogui")
    memory_percent = db.Column(db.Integer, default=95)
    timezone = db.Column(db.String(50), default="Europe/Moscow")
    garbage_collector = db.Column(db.String(50), default="UseSerialGC")
    domain = db.Column(db.String(100), nullable=True)
    srv_record = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        fernet = Fernet(Config.FERNET_KEY.encode())
        self.ssh_password_enc = fernet.encrypt(password.encode()).decode()

    def get_password(self):
        fernet = Fernet(Config.FERNET_KEY.encode())
        return fernet.decrypt(self.ssh_password_enc.encode()).decode()