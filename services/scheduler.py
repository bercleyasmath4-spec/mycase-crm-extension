import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from extensions import db
from models import Client
from services.ai_agent import analyze_all_client_cases
from ringcentral import SDK
from msal import ConfidentialClientApplication
import requests

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

# =====================================================
# 🔧 Load Environment Variables
# =====================================================
RINGCENTRAL_CLIENT_ID = os.getenv("RINGCENTRAL_CLIENT_ID")
RINGCENTRAL_CLIENT_SECRET = os.getenv("RINGCENTRAL_CLIENT_SECRET")
RINGCENTRAL_SERVER_URL = os.getenv("RINGCENTRAL_SERVER_URL", "https://platform.ringcentral.com")
RINGCENTRAL_USERNAME = os.getenv("RINGCENTRAL_USERNAME")
RINGCENTRAL_EXTENSION = os.getenv("RINGCENTRAL_EXTENSION", "")
RINGCENTRAL_PASSWORD = os.getenv("RINGCENTRAL_PASSWORD")

OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID")
OUTLOOK_ADMIN_EMAIL = os.getenv("OUTLOOK_ADMIN_EMAIL")

# =====================================================
# 📱 Initialize RingCentral SDK
# =====================================================
def send_ringcentral_sms(to_number, message):
    """Send SMS using RingCentral admin account."""
    try:
        sdk = SDK(RINGCENTRAL_CLIENT_ID, RINGCENTRAL_CLIENT_SECRET, RINGCENTRAL_SERVER_URL)
        platform = sdk.platform()
        platform.login(RINGCENTRAL_USERNAME, RINGCENTRAL_EXTENSION, RINGCENTRAL_PASSWORD)

        platform.post('/restapi/v1.0/account/~/extension/~/sms', {
            'from': {'phoneNumber': RINGCENTRAL_USERNAME},
            'to': [{'phoneNumber': to_number}],
            'text': message
        })
        logger.info(f"📲 SMS sent to {to_number}: {message}")
    except Exception as e:
        logger.error(f"❌ Failed to send RingCentral SMS: {e}")

# =====================================================
# 📧 Outlook Email Notification
# =====================================================
def send_outlook_email(recipient_email, subject, body):
    """Send an email via Microsoft Graph API using the admin account."""
    try:
        app = ConfidentialClientApplication(
            OUTLOOK_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}",
            client_credential=OUTLOOK_CLIENT_SECRET
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

        if "access_token" in result:
            endpoint = f"https://graph.microsoft.com/v1.0/users/{OUTLOOK_ADMIN_EMAIL}/sendMail"
            email_msg = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": recipient_email}}],
                },
                "saveToSentItems": "true"
            }
            headers = {"Authorization": f"Bearer {result['access_token']}"}
            response = requests.post(endpoint, headers=headers, json=email_msg)

            if response.status_code in [200, 202]:
                logger.info(f"📧 Email sent to {recipient_email}")
            else:
                logger.error(f"❌ Outlook email failed: {response.text}")
        else:
            logger.error("❌ Failed to acquire Outlook token.")
    except Exception as e:
        logger.error(f"❌ Error sending Outlook email: {e}")

# =====================================================
# 🤖 Scheduler AI Analysis + Notification
# =====================================================
def check_all_clients():
    """Background job that analyzes all client cases and sends notifications."""
    from start_app import app
    with app.app_context():
        logger.info("🕒 Running scheduled CasePulse AI client analysis job...")

        try:
            clients = Client.query.all()
            logger.info(f"✅ Found {len(clients)} clients to analyze.")
            if not clients:
                return

            analyze_all_client_cases(clients)

            for client in clients:
                ai_summary = f"New AI analysis update for {client.name}."
                if client.phone:
                    send_ringcentral_sms(client.phone, ai_summary)
                if client.email:
                    send_outlook_email(client.email, "CasePulse AI Update", ai_summary)

            logger.info("✅ CasePulse AI auto-analysis & notifications completed successfully.")
        except Exception as e:
            logger.error(f"❌ Error in scheduled job: {e}")

# =====================================================
# Schedule Job Every 10 Minutes
# =====================================================
scheduler.add_job(func=check_all_clients, trigger="interval", minutes=10)
