import pyotp
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager




@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    totp_secret = db.Column(db.String(32), nullable=False, default=pyotp.random_base32)
    last_used_otp = db.Column(db.String(6), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)  # Флаг администратора

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_totp(self, token):
        if not self.totp_secret or not token:
            return False
        clean_token = token.strip()
        if self.last_used_otp == clean_token:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        if totp.verify(clean_token, valid_window=1):
            self.last_used_otp = clean_token
            db.session.commit()
            return True
        return False


class ServiceTile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    badge = db.Column(db.String(50), default="PUBLIC")
    badge_type = db.Column(db.String(20), default="status-online")  # status-online, status-vpn
    is_admin_only = db.Column(db.Boolean, default=False)           # Видно только админу
    order = db.Column(db.Integer, default=0)
    