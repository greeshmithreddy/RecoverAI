import pandas as pd

from agent import analyze_payment


def get_expected_action(payment):
    """
    Returns the expected recovery action for a synthetic
    payment case.

    These labels represent the safe decision we expect
    RecoverAI to make.
    """

    failure_reason = payment["failure_reason"]
    attempt_count = payment["attempt_count"]
    risk_level = payment["risk_level"]

    # Stop after maximum retry attempts.
    if attempt_count >= 3:
        return "STOP"

    # High-risk payments require human review.
    if risk_level == "high":
        return "ESCALATE"

    # Temporary technical failures can be retried.
    if failure_reason in ["network_error", "bank_timeout"]:
        return "RETRY"

    # Insufficient funds should trigger notification.
    if failure_reason == "insufficient_funds":
        return "NOTIFY"

    # Card declines should be reviewed.
    if failure_reason == "card_declined":
        return "ESCALATE"

    # Unknown failures should be reviewed.
    return "ESCALATE"


def evaluate_agent(df):
    """
    Compares the agent's decisions against expected
    decisions and calculates decision accuracy.
    """

    evaluation_results = []

    for _, payment in df.iterrows():

        prediction = analyze_payment(payment)

        expected_action = get_expected_action(payment)

        evaluation_results.append({
            "transaction_id": payment["transaction_id"],
            "expected_action": expected_action,
            "predicted_action": prediction["action"],
            "correct": (
                prediction["action"] == expected_action
            )
        })

    results = pd.DataFrame(evaluation_results)

    accuracy = (
        results["correct"].mean() * 100
    )

    return results, accuracy