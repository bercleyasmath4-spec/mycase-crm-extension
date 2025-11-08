import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import openai

# -------------------------------------------------
# Load environment variables from flask.env
# -------------------------------------------------
load_dotenv("flask.env")

# -------------------------------------------------
# Initialize Flask app
# -------------------------------------------------
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mycase_crm.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email configuration (for client notifications)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)
db = SQLAlchemy(app)

# -------------------------------------------------
# Initialize OpenAI and OAuth
# -------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")

oauth = OAuth(app)
mycase = oauth.register(
    name="mycase",
    client_id=os.getenv("MYCASE_CLIENT_ID"),
    client_secret=os.getenv("MYCASE_CLIENT_SECRET"),
    authorize_url="https://mycase.com/oauth/authorize",
    access_token_url="https://mycase.com/oauth/token",
    client_kwargs={"scope": "openid profile email"},
)

# -------------------------------------------------
# Database Model
# -------------------------------------------------
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    case_status = db.Column(db.String(200))

    def __repr__(self):
        return f"<Client {self.name}>"

# -------------------------------------------------
# Routes
# -------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")

# ----------------- MyCase OAuth -----------------
@app.route("/login")
def login():
    redirect_uri = url_for("auth", _external=True)
    return mycase.authorize_redirect(redirect_uri)

@app.route("/auth")
def auth():
    try:
        token = mycase.authorize_access_token()
        user = mycase.parse_id_token(token)
        session["user"] = user
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"OAuth authentication failed: {str(e)}"

# ----------------- Dashboard -----------------
@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    clients = Client.query.all()
    return render_template("dashboard.html", user=user, clients=clients)

# ----------------- AI Case Analysis -----------------
@app.route("/analyze_case/<int:client_id>")
def analyze_case(client_id):
    client = Client.query.get_or_404(client_id)

    prompt = f"Analyze the following case details for {client.name}: {client.case_status}"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a legal assistant that summarizes case updates for clients."},
            {"role": "user", "content": prompt}
        ]
    )

    ai_summary = response.choices[0].message.content
    return render_template("analysis.html", client=client, analysis=ai_summary)

# ----------------- Email Notifications -----------------
@app.route("/notify/<int:client_id>")
def notify_client(client_id):
    client = Client.query.get_or_404(client_id)

    msg = Message(
        subject=f"Case Update for {client.name}",
        sender=app.config["MAIL_USERNAME"],
        recipients=[client.email],
        body=f"Dear {client.name},\n\nYour current case status is: {client.case_status}\n\nThank you,\nMyCase CRM Extension"
    )
    mail.send(msg)
    return redirect(url_for("thank_you"))

# -------------------------------------------------
# Main Entry
# -------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
