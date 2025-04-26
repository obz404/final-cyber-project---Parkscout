from app import create_app, db
from flask_dashboard.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    if User.query.filter_by(username=username).first():
        print("⚠️ User already exists.")
    else:
        admin = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully.")