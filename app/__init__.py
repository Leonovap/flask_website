# app/__init__.py
import os
import secrets
from datetime import timedelta
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

#Create DB
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

#create app
def create_app():
    #1 LOAD VARIABLES
    basedir = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(basedir, '.env'))
    
    #2 Create Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'), #html templates folder
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static') #css style file join
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    is_prod = os.getenv('PROD', 'False').lower() == 'true'
    secret_key = os.getenv('SECRET_KEY')
    invite_code = os.getenv('INVITE_SECRET_CODE')

    # На проде запрещаем запуск со слабыми или отсутствующими ключами
    if is_prod:
        if not secret_key or len(secret_key) < 32:
            raise RuntimeError("CRITICAL SECURITY ERROR: SECRET_KEY must be set and >=32 chars in PROD!")
        if not invite_code or len(invite_code) < 16 or invite_code == 'default_secret':
            raise RuntimeError("CRITICAL SECURITY ERROR: Strong INVITE_SECRET_CODE required in PROD!")

    #3 Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'dev-local-fallback-secret-key-999'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # turn off notifications
    # Защита кук и ограничение размера тела запроса (макс 2 МБ — защита от DoS через блокнот)
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = is_prod
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)



    #4 Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)


    #5 Blueprints registration
    from .main.routes import main_bp #routes to main blog contact cv and login/logout
    from .auth.routes import auth_bp #routes for dashboard and links
    from .blog.routes import blog_bp #import routes for blog
    #

    # Добавляем заголовки безопасности ко всем ответам сервера
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    app.register_blueprint(main_bp) #bp main
    app.register_blueprint(auth_bp) #bp auth
    app.register_blueprint(blog_bp) #bp main

     
    #6 Login user loader(flask-login)
    @login_manager.user_loader
    def load_user(user_id):
        from app.auth.models import User
        return User.query.get(int(user_id))


    #7 error handlers:
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403
    
    #8 Auto-creating tables
    with app.app_context():
        db.create_all()

    print(app.url_map)
    
    
    return app
