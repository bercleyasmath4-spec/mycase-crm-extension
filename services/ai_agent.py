import logging
from openai import OpenAI

# Initialize logging
logger = logging.getLogger(__name__)

# ✅ Initialize OpenAI client once
try:
    client = OpenAI()
    logger.info("✅ AI Agent: OpenAI client initialized successfully.")
except Exception as e:
    logger.error(f"❌ Failed to initialize OpenAI client: {e}")
    client = None


# ================================
# Analyze a single client's case
# ================================
def analyze_client_cases(client_obj):
    """
    Uses OpenAI to generate an AI summary of a client's case history.
    """
    if not client:
        logger.error("❌ OpenAI client not initialized.")
        return "AI analysis unavailable at this time."

    try:
        # Build prompt based on client's details
        prompt = f"""
        You are an AI legal assistant. Summarize this client's case data clearly and professionally.

        Client Name: {client_obj.name}
        Email: {client_obj.email}
        Phone: {client_obj.phone}
        Case updates:
        {', '.join([cu.summary for cu in client_obj.case_updates]) if client_obj.case_updates else "No updates yet."}

        Provide a short analysis (1–2 sentences) on the case status or next steps.
        """

        # Use OpenAI's API
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        summary = response.output[0].content[0].text.strip()
        logger.info(f"🤖 AI Analysis complete for {client_obj.name}")
        return summary

    except Exception as e:
        logger.error(f"❌ Error analyzing client {client_obj.name}: {e}")
        return "Error: AI analysis could not be completed."


# ================================
# Analyze all clients (for scheduler)
# ================================
def analyze_all_client_cases(db, Client, CaseUpdate):
    """
    Scheduler uses this to analyze all clients periodically.
    """
    from flask import current_app
    with current_app.app_context():
        clients = Client.query.all()
        for c in clients:
            summary = analyze_client_cases(c)
            if summary:
                new_update = CaseUpdate(client_id=c.id, summary=summary)
                db.session.add(new_update)
        db.session.commit()
        logger.info("🧠 Scheduled AI case analysis completed for all clients.")
