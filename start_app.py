import os
import logging
from flask import Flask, render_template
from flask_login import LoginManager
from extensions import db
from models import User
from services.scheduler import init_scheduler

# =========================
#  Flask App Initialization
# =========================
app = Flask(__name__, instance_relative_config=True)

# Ensure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# =========================
#  Configuration
# =========================
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret_key")

# Database: Ensure absolute path for SQLite
db_path = os.path.join(app.instance_path, "mycasecrm.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# =========================
#  Login Manager
# =========================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
#  Logging
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
#  Blueprints
# =========================
try:
    from routes.auth import auth_bp
    from routes.dashboard import dash_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dash_bp, url_prefix="/dashboard")
    app.register_blueprint(api_bp, url_prefix="/api")

    logger.info("✅ Blueprints registered successfully.")
except Exception as e:
    logger.warning(f"⚠️ Route import issue: {e}")

# =========================
#  Scheduler
# =========================
try:
    init_scheduler(app)
    logger.info("✅ Scheduler started successfully.")
except Exception as e:
    logger.warning(f"⚠️ Scheduler not found. Skipping background tasks. ({e})")

# =========================
#  Routes
# =========================
@app.route("/")
def home():
    return render_template("dashboard.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# =========================
#  Database + Admin User
# =========================
def ensure_admin_exists():
    """Ensure the admin user exists in the database."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@casepulseai.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        logger.info("✅ Admin user created successfully.")
    else:
        logger.info("✅ Admin user already exists.")

with app.app_context():
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.create_all()
    ensure_admin_exists()
    logger.info("✅ Database initialized and checked for admin user.")

# =========================
#  Run App
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
