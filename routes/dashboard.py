from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Client, CaseUpdate, Message
from services.ai_agent import analyze_client_cases

dash_bp = Blueprint("dash_bp", __name__)

# ==========================
# Dashboard route
# ==========================
@dash_bp.route("/dashboard")
@login_required
def dashboard():
    clients = Client.query.all()
    case_updates = CaseUpdate.query.order_by(CaseUpdate.created_at.desc()).limit(5).all()
    messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", clients=clients, case_updates=case_updates, messages=messages)

# ==========================
# Add new client
# ==========================
@dash_bp.route("/dashboard/add_client", methods=["POST"])
@login_required
def add_client():
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")

    new_client = Client(name=name, phone=phone, email=email)
    db.session.add(new_client)
    db.session.commit()

    flash("✅ Client added successfully!", "success")
    return redirect(url_for("dash_bp.dashboard"))

# ==========================
# Delete client
# ==========================
@dash_bp.route("/dashboard/delete_client/<int:client_id>", methods=["POST"])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("🗑️ Client deleted successfully.", "info")
    return redirect(url_for("dash_bp.dashboard"))

# ==========================
# Client details
# ==========================
@dash_bp.route("/dashboard/client/<int:client_id>")
@login_required
def client_details(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template("client_details.html", client=client)

# ==========================
# AI Case Analysis
# ==========================
@dash_bp.route("/dashboard/analyze", methods=["POST"])
@login_required
def analyze_cases():
    clients = Client.query.all()
    for client in clients:
        analysis_result = analyze_client_cases(client)
        new_update = CaseUpdate(client_id=client.id, summary=analysis_result)
        db.session.add(new_update)
    db.session.commit()

    flash("🤖 AI analysis completed for all clients!", "success")
    return redirect(url_for("dash_bp.dashboard"))
