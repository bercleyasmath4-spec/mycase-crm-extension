# routes/dashboard_routes.py
from flask import Blueprint, render_template

dash_bp = Blueprint("dash_bp", __name__)

@dash_bp.route("/dashboard")
def dashboard():
    """Main dashboard page"""
    return render_template("dashboard.html")
