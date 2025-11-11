import os
import logging
from openai import OpenAI

# Configure logger for this service
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure logs also show up on Render/console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize OpenAI client
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")

    # ✅ New SDK initialization — no 'proxies' argument needed
    client = OpenAI(api_key=openai_api_key)

    logger.info("✅ AI Agent: OpenAI client initialized successfully.")

except Exception as e:
    logger.error(f"❌ Failed to initialize OpenAI client: {e}")
    client = None


def analyze_case_text(case_text: str) -> str:
    """
    Analyze a client case description and generate a professional summary.
    Uses GPT-4 or latest available model.
    """
    if not client:
        logger.error("❌ OpenAI client not initialized — cannot analyze case text.")
        return "AI service unavailable."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant for a law firm CRM system. "
                        "Summarize case updates, identify important legal details, "
                        "and respond in clear, professional language."
                    ),
                },
                {"role": "user", "content": case_text},
            ],
            temperature=0.5,
        )

        summary = response.choices[0].message.content.strip()
        logger.info("✅ Successfully analyzed case text.")
        return summary

    except Exception as e:
        logger.error(f"❌ Error during case analysis: {e}")
        return "An error occurred while analyzing the case."


def generate_client_notification(case_summary: str, client_name: str) -> str:
    """
    Generate a concise SMS-style message for notifying the client about their case.
    """
    if not client:
        logger.error("❌ OpenAI client not initialized — cannot generate message.")
        return "Notification service unavailable."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant for a law firm CRM that writes polite, "
                        "concise text messages to clients about their cases."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a brief and professional update text message for "
                        f"client {client_name} summarizing this case update:\n\n{case_summary}"
                    ),
                },
            ],
            temperature=0.7,
        )

        notification = response.choices[0].message.content.strip()
        logger.info("✅ Successfully generated client notification.")
        return notification

    except Exception as e:
        logger.error(f"❌ Error generating client notification: {e}")
        return "An error occurred while generating the notification."
