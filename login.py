import getpass
from app import create_app, db
from app.auth.models import User

app = create_app()

with app.app_context():
    db.create_all()

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)

    user.set_password(password)
    db.session.commit()
    print(f"[+] Пользователь '{username}' успешно сохранен в базу!")