from start_app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@casepulseai.com").first():
        admin = User(
            email="admin@casepulseai.com",
            password_hash=generate_password_hash("your_admin_password"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully.")
