from flask import Blueprint, request, redirect, render_template, flash, url_for, Flask
from flask_login import login_user, logout_user, login_required
from app.auth.models import User
from app.auth.forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm() #make form exemplar
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.dashboard'))
        else:
          flash('Wrong password or username')
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
   