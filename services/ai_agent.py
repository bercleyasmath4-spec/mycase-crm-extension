import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = None

def init_openai():
    """Initialize the OpenAI client safely."""
    global client
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("❌ Missing OPENAI_API_KEY in environment variables.")
        return None

    try:
        client = OpenAI(api_key=api_key)
        logger.info("✅ AI Agent: OpenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
        client = None

    return client

def ask_openai(prompt: str):
    """Send a prompt to the OpenAI model and return the response text."""
    global client

    if client is None:
        init_openai()
    if client is None:
        return "⚠️ OpenAI client not initialized. Please check your API key."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ OpenAI API error: {e}")
        return f"⚠️ Error communicating with AI: {e}"
# ======================================================
# ✅ Compatibility wrapper for scheduler integration
# ======================================================
def analyze_all_client_cases():
    """Wrapper to maintain backward compatibility with scheduler."""
    from services.mycase_api import get_all_client_data  # adjust if different
    from services.notifications import notify_client     # adjust if different

    try:
        logger.info("🔄 Running case analysis for all clients...")
        clients = get_all_client_data()
        if not clients:
            logger.warning("No clients found to analyze.")
            return

        for client in clients:
            result = analyze_client_case(client)
            logger.info(f"✅ Analysis complete for client: {client.get('name', 'Unknown')}")
            notify_client(client, result)

    except Exception as e:
        logger.error(f"❌ Failed to analyze all client cases: {e}")

def analyze_client_cases(client_id):
    """
    Compatibility wrapper for dashboard imports.
    Runs AI analysis for a specific client ID using analyze_all_client_cases().
    """
    return analyze_all_client_cases(client_id=client_id)
