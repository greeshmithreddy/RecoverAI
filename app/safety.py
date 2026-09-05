ALLOWED_ACTIONS = {
    "RETRY",
    "NOTIFY",
    "ESCALATE",
    "STOP"
}


def validate_action(payment, action):

    attempt_count = payment["attempt_count"]
    risk_level = payment["risk_level"]

    if action not in ALLOWED_ACTIONS:
        return {
            "allowed": False,
            "final_action": "ESCALATE",
            "reason": "Unknown AI action. Safely escalated for human review."
        }

    if attempt_count >= 3:
        return {
            "allowed": action == "STOP",
            "final_action": "STOP",
            "reason": "Recovery stopped: maximum retry limit reached."
        }

    if risk_level == "high" and action == "RETRY":
        return {
            "allowed": False,
            "final_action": "ESCALATE",
            "reason": "AI retry blocked: high-risk payment requires human review."
        }

    return {
        "allowed": True,
        "final_action": action,
        "reason": "Action passed safety validation."
    }