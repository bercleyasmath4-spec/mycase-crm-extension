import os
import logging
from ringcentral import SDK
from msal import ConfidentialClientApplication
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================
# RINGCENTRAL SETUP
# ============================
RINGCENTRAL_CLIENT_ID = os.getenv("RINGCENTRAL_CLIENT_ID")
RINGCENTRAL_CLIENT_SECRET = os.getenv("RINGCENTRAL_CLIENT_SECRET")
RINGCENTRAL_SERVER_URL = os.getenv("RINGCENTRAL_SERVER_URL")
RINGCENTRAL_REDIRECT_URI = os.getenv("RINGCENTRAL_REDIRECT_URI")

# ============================
# OUTLOOK SETUP
# ============================
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
OUTLOOK_REDIRECT_URI = os.getenv("OUTLOOK_REDIRECT_URI")
OUTLOOK_AUTHORITY = "https://login.microsoftonline.com/common"
OUTLOOK_SCOPES = ["https://graph.microsoft.com/.default"]

# ============================
# RINGCENTRAL FUNCTIONS
# ============================
def send_sms(phone_number, message_text):
    """Send an SMS using RingCentral API."""
    try:
        sdk = SDK(RINGCENTRAL_CLIENT_ID, RINGCENTRAL_CLIENT_SECRET, RINGCENTRAL_SERVER_URL)
        platform = sdk.platform()
        platform.login(jwt=os.getenv("RINGCENTRAL_JWT"))  # You can generate a JWT for your app
        response = platform.post('/restapi/v1.0/account/~/extension/~/sms', {
            'from': {'phoneNumber': os.getenv("RINGCENTRAL_PHONE")},
            'to': [{'phoneNumber': phone_number}],
            'text': message_text
        })
        logger.info(f"✅ SMS sent to {phone_number}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to send SMS: {e}")
        return None

# ============================
# OUTLOOK EMAIL FUNCTIONS
# ============================
def get_outlook_token():
    """Authenticate and retrieve access token for Outlook Graph API."""
    app = ConfidentialClientApplication(
        OUTLOOK_CLIENT_ID,
        authority=OUTLOOK_AUTHORITY,
        client_credential=OUTLOOK_CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=OUTLOOK_SCOPES)
    if "access_token" in result:
        return result["access_token"]
    else:
        logger.error(f"❌ Outlook auth failed: {result.get('error_description')}")
        return None

def send_outlook_email(recipient, subject, content):
    """Send an email using Outlook Graph API."""
    token = get_outlook_token()
    if not token:
        return None

    url = "https://graph.microsoft.com/v1.0/users/me/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": content},
            "toRecipients": [{"emailAddress": {"address": recipient}}]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        logger.info(f"✅ Email sent to {recipient}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return None
