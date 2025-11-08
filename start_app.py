# start_app.py - CasePulse AI (production-ready skeleton)
import os
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, session,
    url_for, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Optional imports (only if you install packages)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()  # read .env in development; Render uses environment

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///mycase.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# External provider config (all via env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # optional
OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD")
RINGCENTRAL_CLIENT_ID = os.getenv("RINGCENTRAL_CLIENT_ID")
RINGCENTRAL_CLIENT_SECRET = os.getenv("RINGCENTRAL_CLIENT_SECRET")
RINGCENTRAL_SERVER = os.getenv("RINGCENTRAL_SERVER", "https://platform.ringcentral.com")
RINGCENTRAL_REDIRECT = os.getenv("RINGCENTRAL_REDIRECT_URI")  # set on Render when live

MYCASE_CLIENT_ID = os.getenv("MYCASE_CLIENT_ID")
MYCASE_CLIENT_SECRET = os.getenv("MYCASE_CLIENT_SECRET")
MYCASE_AUTH_URL = os.getenv("MYCASE_AUTH_URL")  # e.g. https://www.mycase.com/oauth/authorize
MYCASE_TOKEN_URL = os.getenv("MYCASE_TOKEN_URL")  # e.g. https://www.mycase.com/oauth/token
MYCASE_REDIRECT = os.getenv("MYCASE_REDIRECT_URI")  # set to your deployed URL + /mycase/callback

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

# Initialize optional OpenAI client
openai_client = None
if OPENAI_API_KEY and OpenAI is not None:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# DB models
class OAuthToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(64), nullable=False)
    token_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(200), unique=False, nullable=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(40))
    phone_carrier = db.Column(db.String(200), nullable=True)
    case_number = db.Column(db.String(200))
    last_status = db.Column(db.String(1000), nullable=True)
    preferred_language = db.Column(db.String(8), default="english")
    notifications_paused = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ------------------------
# Utilities
# ------------------------
def send_outlook_email(to_email, subject, body_text):
    """Primary email via Outlook (Office365 SMTP)."""
    if not OUTLOOK_EMAIL or not OUTLOOK_PASSWORD:
        app.logger.warning("Outlook credentials not set.")
        return False, "No credentials"
    try:
        msg = MIMEMultipart()
        msg["From"] = OUTLOOK_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain"))
        with smtplib.SMTP(os.getenv("OUTLOOK_SMTP", "smtp.office365.com"), int(os.getenv("OUTLOOK_SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
            server.send_message(msg)
        return True, "Sent"
    except Exception as e:
        app.logger.exception("Outlook send error")
        return False, str(e)

def send_ringcentral_sms(to_number, message):
    """
    Placeholder to send SMS via RingCentral REST API.
    When you have client_id/secret, implement OAuth server-side then call messaging endpoint.
    This function uses placeholders; replace with real OAuth token logic later.
    """
    if not (RINGCENTRAL_CLIENT_ID and RINGCENTRAL_CLIENT_SECRET):
        app.logger.warning("RingCentral not configured.")
        return False, "not configured"
    # Placeholder: in production you'd acquire an access token then POST to /restapi/v1.0/account/~/extension/~/messaging
    app.logger.info("RingCentral send placeholder - implement OAuth/token flow")
    return False, "placeholder"

def generate_ai_message(client_name, case_text, language="english"):
    """Use OpenAI to craft multilingual message; fallback to plain text if no key."""
    if not openai_client:
        return f"Hello {client_name}: {case_text}"
    try:
        # Use ChatCompletion or appropriate modern client; keep it simple here
        resp = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role":"system","content":"You are a helpful legal assistant."},
                      {"role":"user","content":f"Write a 1-2 sentence client-friendly message in {language}: {case_text}"}],
            max_tokens=200,
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        app.logger.exception("OpenAI error")
        return f"Hello {client_name}: {case_text}"

# ------------------------
# Routes - Public / Admin
# ------------------------
@app.route("/")
def index():
    connected = bool(OAuthToken.query.filter_by(provider="mycase").first())
    return render_template("mycase_auth.html", connected=connected)

# Admin-only basic login (env-based)
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session["admin"] = True
            flash("Admin login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

@app.route("/admin/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    clients = ClientRecord.query.order_by(ClientRecord.created_at.desc()).all()
    tokens = OAuthToken.query.all()
    return render_template("dashboard.html", clients=clients, tokens=tokens)

# Subscribe/unsubscribe endpoints for CRM integration
@app.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json() or request.form
    client = ClientRecord(
        client_id=data.get("client_id"),
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        case_number=data.get("case_number"),
        preferred_language=data.get("preferred_language", "english")
    )
    db.session.add(client)
    db.session.commit()
    return jsonify({"message":"subscribed","id":client.id})

@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json() or request.form
    client = ClientRecord.query.filter_by(client_id=data.get("client_id")).first()
    if client:
        db.session.delete(client)
        db.session.commit()
    return jsonify({"message":"unsubscribed"})

# Manual trigger route
@app.route("/trigger-check", methods=["POST"])
def trigger_check():
    # For demo: send test notifications to all clients (use carefully)
    clients = ClientRecord.query.all()
    results = []
    for c in clients:
        case_text = "Automated check - no real MyCase data (placeholder)."
        msg = generate_ai_message(c.name, case_text, c.preferred_language)
        email_ok, email_msg = send_outlook_email(c.email, f"Case update: {c.case_number or 'N/A'}", msg)
        sms_ok, sms_msg = send_ringcentral_sms(c.phone, msg)
        results.append({"client": c.id, "email": email_ok, "sms": sms_ok})
    return jsonify({"sent": results})

# ------------------------
# MyCase OAuth placeholder routes
# ------------------------
@app.route("/mycase/login")
def mycase_login():
    # Redirect to MyCase authorize URL (constructed from env variables). If missing env -> show informative page.
    if not (MYCASE_CLIENT_ID and MYCASE_AUTH_URL and MYCASE_REDIRECT):
        flash("MyCase OAuth not configured yet. Add credentials to environment.", "warning")
        return redirect(url_for("index"))
    params = {
        "client_id": MYCASE_CLIENT_ID,
        "redirect_uri": MYCASE_REDIRECT,
        "response_type": "code",
        "scope": "openid profile email"
    }
    auth_url = MYCASE_AUTH_URL + "?" + "&".join(f"{k}={requests.utils.quote(str(v))}" for k,v in params.items())
    return redirect(auth_url)

@app.route("/mycase/callback")
def mycase_callback():
    # Exchange code for token - placeholder implementation
    code = request.args.get("code")
    if not code:
        flash("No code returned from MyCase.", "danger")
        return redirect(url_for("index"))
    if not (MYCASE_CLIENT_ID and MYCASE_CLIENT_SECRET and MYCASE_TOKEN_URL and MYCASE_REDIRECT):
        flash("MyCase token exchange not configured in environment.", "danger")
        return redirect(url_for("index"))
    # Actual implementation: POST to MYCASE_TOKEN_URL with code/client credentials
    # Save token to DB (placeholder)
    token_data = {"access_token":"placeholder","scope":"openid","received_at": datetime.utcnow().isoformat()}
    ot = OAuthToken(provider="mycase", token_json=json.dumps(token_data))
    db.session.add(ot)
    db.session.commit()
    flash("MyCase connected (placeholder stored).", "success")
    return redirect(url_for("dashboard"))

# ------------------------
# Settings pages
# ------------------------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        # Example: save preferences - for now we just flash
        flash("Settings saved (not persisted in this demo).", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html")

# ------------------------
# Error handling
# ------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Server error."), 500

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    # Use 0.0.0.0 for Render
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
