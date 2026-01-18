# app/__init__.py
import os
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

#Create DB
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

#create app
def create_app():
    #1 LOAD VARIABLES
    load_dotenv()
    
    #2 Create Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'), #html templates folder
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static') #css style file join
    )

    #3 Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # turn off notifications
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True



    #4 Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)

    #5 Blueprints registration
    from .main.routes import main_bp #routes to main blog contact cv and login/logout
    from .auth.routes import auth_bp #routes for dashboard and links
    from .blog.routes import blog_bp #import routes for blog
    #
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
