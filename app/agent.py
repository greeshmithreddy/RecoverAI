import json
import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ALLOWED_ACTIONS = {
    "RETRY",
    "NOTIFY",
    "ESCALATE",
    "STOP"
}


def analyze_payment(payment):

    prompt = f"""
You are the AI decision engine for RecoverAI,
an AI revenue recovery system for online merchants.

Analyze this failed payment:

Transaction ID: {payment["transaction_id"]}
Amount: ₹{payment["amount"]}
Payment method: {payment["payment_method"]}
Failure reason: {payment["failure_reason"]}
Attempt count: {payment["attempt_count"]}
Previous success rate: {payment["previous_success_rate"]}
Risk level: {payment["risk_level"]}

Choose exactly ONE recovery action:

RETRY
NOTIFY
ESCALATE
STOP

Rules:
- If attempts are 3 or more, choose STOP.
- High-risk payments should not be automatically retried.
- Temporary technical failures may use RETRY.
- Insufficient funds should generally use NOTIFY.
- Card declines should generally use ESCALATE.
- Unknown failures should use ESCALATE.

Return ONLY valid JSON:

{{
    "diagnosis": "short diagnosis",
    "action": "RETRY/NOTIFY/ESCALATE/STOP",
    "confidence": 0.0,
    "reason": "short explanation"
}}

confidence must be between 0 and 1.
"""

    try:
        response = client.interactions.create(
    model="gemini-3.6-flash",
    input=prompt
)

        text = response.output_text.strip()

        # Remove markdown code fences if Gemini adds them
        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        result = json.loads(text)

        action = result.get("action", "ESCALATE")

        # Deterministic safety fallback
        if action not in ALLOWED_ACTIONS:
            action = "ESCALATE"

        return {
            "diagnosis": result.get(
                "diagnosis",
                "Unable to determine failure"
            ),
            "action": action,
            "confidence": float(
                result.get("confidence", 0.50)
            ),
            "reason": result.get(
                "reason",
                "The payment requires further review."
            )
        }

    except Exception as e:

        print("AI ERROR:", repr(e))

        return {
            "diagnosis": "AI analysis unavailable",
            "action": "ESCALATE",
            "confidence": 0.0,
            "reason": "AI analysis failed, so the payment was safely escalated for human review."
        }