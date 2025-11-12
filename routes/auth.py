from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import User
from extensions import db


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ===============================
# LOGIN ROUTE
# ===============================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("✅ Logged in successfully!", "success")
            return redirect(url_for("dash_bp.dashboard"))
        else:
            flash("❌ Invalid email or password.", "danger")

    return render_template("login.html")

# ===============================
# LOGOUT ROUTE
# ===============================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("✅ You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))
