import os
import logging
from datetime import datetime
from flask import Flask, render_template
from flask_migrate import Migrate
from extensions import db, login_manager
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# =======================
# Load environment variables
# =======================
load_dotenv()

# =======================
# Configure logging
# =======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =======================
# Flask app setup
# =======================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")

# Ensure database folder exists
os.makedirs("instance", exist_ok=True)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "mycasecrm.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Register current datetime as a Jinja global
app.jinja_env.globals["now"] = datetime.now

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# =======================
# Flask-Login Configuration
# =======================
from models import User

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

# =======================
# Register Blueprints
# =======================
try:
    from routes.auth import auth_bp
    from routes.dashboard import dash_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    logger.info("✅ Blueprints registered successfully.")
except Exception as e:
    logger.warning(f"⚠️ Route import issue: {e}")

# =======================
# AI Agent + Scheduler
# =======================
try:
    from services.scheduler import scheduler, check_all_clients
    scheduler.start()
    logger.info("✅ Scheduler started successfully.")
except Exception as e:
    logger.warning(f"⚠️ Scheduler not found. Skipping background tasks. ({e})")

# =======================
# Ensure default admin
# =======================
def ensure_admin_exists():
    """Ensure a default admin user exists."""
    with app.app_context():
        admin_email = "admin@casepulseai.com"
        admin_password = "admin123"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            hashed_password = generate_password_hash(admin_password)
            new_admin = User(email=admin_email, password_hash=hashed_password, role="admin")
            db.session.add(new_admin)
            db.session.commit()
            print("👑 Default admin created — admin@casepulseai.com / admin123")
        else:
            print("✅ Admin user already exists.")

# =======================
# Routes
# =======================
@app.route("/")
def home():
    """Home route — dashboard if logged in, index otherwise."""
    from flask_login import current_user
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")

@app.route("/about")
def about():
    """About page route."""
    return render_template("about.html")

# =======================
# Main App Launch
# =======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_admin_exists()
        logger.info("✅ Database initialized and checked for admin user.")
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
