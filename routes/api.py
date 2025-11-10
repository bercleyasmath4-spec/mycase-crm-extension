from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
from models import db, Client, CaseUpdate

api_bp = Blueprint("api", __name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY)

@api_bp.route("/analyze", methods=["POST"])
def analyze_update():
    """Endpoint for analyzing text manually via dashboard or API."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that analyzes legal case updates for clients."},
                {"role": "user", "content": data["text"]}
            ],
            max_tokens=150
        )
        result = response.choices[0].message.content.strip()
        return jsonify({"analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/clients", methods=["GET"])
def list_clients():
    """List all clients for the admin dashboard."""
    clients = Client.query.all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone_number
    } for c in clients])

@api_bp.route("/case-update", methods=["POST"])
def create_case_update():
    """Add a new case update to the database."""
    data = request.get_json()
    if not all(k in data for k in ("client_id", "description")):
        return jsonify({"error": "Missing required fields"}), 400
    new_update = CaseUpdate(
        client_id=data["client_id"],
        description=data["description"]
    )
    db.session.add(new_update)
    db.session.commit()
    return jsonify({"message": "Case update added successfully"})
