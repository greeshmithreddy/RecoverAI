def simulate_recovery(payment, action):
    """
    Simulates the result of a recovery action.

    This is a synthetic simulation.
    No real payment is processed.
    """

    failure_reason = payment["failure_reason"]
    attempt_count = payment["attempt_count"]
    previous_success_rate = payment["previous_success_rate"]

    # Stop if the payment has already reached the retry limit.
    if attempt_count >= 3:
        return {
            "success": False,
            "result": "Retry limit reached",
            "recovered_amount": 0
        }

    # Retry temporary technical failures.
    if action == "RETRY":
        if failure_reason in ["network_error", "bank_timeout"]:
            if previous_success_rate >= 0.80:
                return {
                    "success": True,
                    "result": "Payment recovered successfully",
                    "recovered_amount": payment["amount"]
                }

        return {
            "success": False,
            "result": "Retry unsuccessful",
            "recovered_amount": 0
        }

    # Notify customers when the likely problem is insufficient funds.
    if action == "NOTIFY":
        if failure_reason == "insufficient_funds":
            return {
                "success": True,
                "result": "Customer notified for payment recovery",
                "recovered_amount": payment["amount"]
            }

        return {
            "success": False,
            "result": "Notification did not recover payment",
            "recovered_amount": 0
        }

    # Escalation does not automatically recover money.
    if action == "ESCALATE":
        return {
            "success": False,
            "result": "Case escalated for human review",
            "recovered_amount": 0
        }

    # STOP means no further recovery attempt.
    if action == "STOP":
        return {
            "success": False,
            "result": "Recovery stopped safely",
            "recovered_amount": 0
        }

    return {
        "success": False,
        "result": "Unknown action rejected",
        "recovered_amount": 0
    }