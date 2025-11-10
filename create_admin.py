from start_app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin_email = "admin@casepulseai.com"
    admin_password = "admin123"

    # Hash the password securely
    hashed_password = generate_password_hash(admin_password)

    # Check if admin already exists
    admin = User.query.filter_by(email=admin_email).first()

    if not admin:
        new_admin = User(email=admin_email, hashed_password=hashed_password, role="admin")
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
    else:
        print("ℹ️ Admin user already exists.")
