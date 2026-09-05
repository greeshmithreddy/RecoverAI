import streamlit as st
import pandas as pd

from data import create_payment_dataset
from agent import analyze_payment
from safety import validate_action
from simulator import simulate_recovery


# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="RecoverAI",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# Baseline Decision Engine
# =========================================================
# This deterministic engine is used for batch evaluation.
# It does NOT consume Gemini API quota.
# =========================================================

def baseline_action(payment):

    if payment["attempt_count"] >= 3:
        return "STOP"

    if payment["risk_level"] == "high":
        return "ESCALATE"

    if payment["failure_reason"] in [
        "network_error",
        "bank_timeout"
    ]:
        return "RETRY"

    if payment["failure_reason"] == "insufficient_funds":
        return "NOTIFY"

    if payment["failure_reason"] == "card_declined":
        return "ESCALATE"

    return "ESCALATE"


# =========================================================
# AI Evaluation
# =========================================================

def evaluate_ai_decision(payment, ai_action):

    expected = baseline_action(payment)

    return {
        "expected_action": expected,
        "ai_action": ai_action,
        "correct": ai_action == expected
    }


# =========================================================
# Load Synthetic Dataset
# =========================================================

df = create_payment_dataset()


# =========================================================
# Batch Processing
# =========================================================
# Deterministic processing is used here so that the dashboard
# does not consume Gemini API quota on every page refresh.
# =========================================================

batch_results = []

for _, payment in df.iterrows():

    action = baseline_action(payment)

    safety = validate_action(
        payment,
        action
    )

    final_action = safety["final_action"]

    outcome = simulate_recovery(
        payment,
        final_action
    )

    batch_results.append({
        "transaction_id": payment["transaction_id"],
        "amount": payment["amount"],
        "failure_reason": payment["failure_reason"],
        "risk_level": payment["risk_level"],
        "attempt_count": payment["attempt_count"],
        "action": final_action,
        "safety_allowed": safety["allowed"],
        "success": outcome["success"],
        "recovered_amount": outcome["recovered_amount"],
        "result": outcome["result"]
    })


results_df = pd.DataFrame(batch_results)


# =========================================================
# Metrics
# =========================================================

total_at_risk = results_df["amount"].sum()

total_recovered = results_df["recovered_amount"].sum()

recovery_rate = (
    total_recovered / total_at_risk * 100
    if total_at_risk > 0
    else 0
)

safety_compliance = (
    results_df["safety_allowed"].mean() * 100
)

average_attempts = df["attempt_count"].mean()


# =========================================================
# Header
# =========================================================

st.title("💰 RecoverAI")

st.subheader("AI-Powered Revenue Recovery Agent")

st.write(
    "RecoverAI analyzes failed payments, determines the most "
    "appropriate recovery strategy, validates the action through "
    "a safety layer, and measures the recovery outcome."
)


# =========================================================
# Main KPI Dashboard
# =========================================================

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Payments Analyzed",
        len(df)
    )

with col2:

    st.metric(
        "Revenue at Risk",
        f"₹{total_at_risk:,.0f}"
    )

with col3:

    st.metric(
        "Revenue Recovered",
        f"₹{total_recovered:,.0f}"
    )

with col4:

    st.metric(
        "Recovery Rate",
        f"{recovery_rate:.1f}%"
    )


# =========================================================
# Recovery Performance
# =========================================================

st.header("📊 Recovery Performance")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Safety Compliance",
        f"{safety_compliance:.1f}%"
    )

with col2:

    st.metric(
        "Average Attempts",
        f"{average_attempts:.2f}"
    )

with col3:

    st.metric(
        "AI Mode",
        "On-demand"
    )


st.caption(
    "Batch metrics use the controlled evaluation dataset. "
    "Gemini is invoked only for individual payment analysis."
)


# =========================================================
# Recovery by Failure Type
# =========================================================

st.subheader("Recovery by Failure Type")

grouped = (
    results_df
    .groupby("failure_reason")
    .agg(
        payments=("transaction_id", "count"),
        revenue_at_risk=("amount", "sum"),
        recovered=("recovered_amount", "sum")
    )
    .reset_index()
)

grouped["recovery_rate"] = (
    grouped["recovered"]
    / grouped["revenue_at_risk"]
    * 100
)

grouped = grouped.rename(
    columns={
        "failure_reason": "Failure Type",
        "payments": "Payments",
        "revenue_at_risk": "Revenue at Risk",
        "recovered": "Recovered",
        "recovery_rate": "Recovery Rate"
    }
)

grouped["Revenue at Risk"] = grouped["Revenue at Risk"].apply(
    lambda x: f"₹{x:,.0f}"
)

grouped["Recovered"] = grouped["Recovered"].apply(
    lambda x: f"₹{x:,.0f}"
)

grouped["Recovery Rate"] = grouped["Recovery Rate"].apply(
    lambda x: f"{x:.1f}%"
)

st.dataframe(
    grouped,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# Payment Inspector
# =========================================================

st.divider()

st.header("🔎 Payment Inspector")

transaction_ids = df["transaction_id"].tolist()

selected_id = st.selectbox(
    "Select a failed payment",
    transaction_ids
)

selected_payment = df[
    df["transaction_id"] == selected_id
].iloc[0]


# =========================================================
# Payment Information
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Amount",
        f"₹{selected_payment['amount']:,.0f}"
    )

with col2:

    st.metric(
        "Attempts",
        selected_payment["attempt_count"]
    )

with col3:

    st.metric(
        "Previous Success",
        f"{selected_payment['previous_success_rate'] * 100:.0f}%"
    )

with col4:

    st.metric(
        "Risk",
        selected_payment["risk_level"].upper()
    )


st.write(
    f"**Payment Method:** "
    f"{selected_payment['payment_method']}"
)

st.write(
    f"**Failure Reason:** "
    f"`{selected_payment['failure_reason']}`"
)


# =========================================================
# AI Analysis
# =========================================================

st.subheader("🤖 AI Analysis")

st.write(
    "Gemini analyzes the selected payment and recommends "
    "a recovery strategy."
)


if st.button(
    "Analyze with Gemini",
    type="primary"
):

    with st.spinner(
        "Gemini is analyzing the payment..."
    ):

        ai_result = analyze_payment(
            selected_payment
        )

    st.session_state["ai_result"] = ai_result

    st.session_state["ai_transaction"] = selected_id


# =========================================================
# Display AI Result
# =========================================================

if (
    "ai_result" in st.session_state
    and st.session_state.get("ai_transaction") == selected_id
):

    ai_result = st.session_state["ai_result"]


    # -----------------------------------------------------
    # Diagnosis
    # -----------------------------------------------------

    st.write("### Diagnosis")

    st.info(
        ai_result["diagnosis"]
    )


    # -----------------------------------------------------
    # AI Recommendation
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Recommended Action**")

        st.success(
            ai_result["action"]
        )

    with col2:

        st.write("**AI Confidence**")

        st.metric(
            "Confidence",
            f"{ai_result['confidence'] * 100:.0f}%"
        )


    # -----------------------------------------------------
    # AI Reasoning
    # -----------------------------------------------------

    st.write(
        "### Why RecoverAI chose this action"
    )

    st.write(
        ai_result["reason"]
    )


    # =====================================================
    # Safety Validation
    # =====================================================

    st.subheader("🛡️ Safety Validation")

    safety_result = validate_action(
        selected_payment,
        ai_result["action"]
    )


    if safety_result["allowed"]:

        st.success(
            f"✅ Action allowed — "
            f"{safety_result['reason']}"
        )

    else:

        st.error(
            f"🚫 AI action overridden — "
            f"{safety_result['reason']}"
        )


    # The safety layer determines the final action.
    final_action = safety_result["final_action"]


    # =====================================================
    # Recovery Simulation
    # =====================================================

    st.subheader("💳 Recovery Outcome")

    outcome = simulate_recovery(
        selected_payment,
        final_action
    )


    if outcome["success"]:

        st.success(
            f"✅ {outcome['result']}"
        )

        st.metric(
            "Recovered Amount",
            f"₹{outcome['recovered_amount']:,.0f}"
        )

    else:

        st.warning(
            f"⚠️ {outcome['result']}"
        )

        st.metric(
            "Recovered Amount",
            "₹0"
        )


    # =====================================================
    # Audit Record
    # =====================================================

    st.subheader("📋 Audit Record")

    audit_record = {
        "Transaction": selected_id,
        "AI Diagnosis": ai_result["diagnosis"],
        "AI Action": ai_result["action"],
        "AI Confidence": (
            f"{ai_result['confidence'] * 100:.0f}%"
        ),
        "Safety Allowed": safety_result["allowed"],
        "Safety Decision": safety_result["reason"],
        "Final Action": final_action,
        "Outcome": outcome["result"],
        "Recovered Amount": (
            f"₹{outcome['recovered_amount']:,.0f}"
        )
    }

    st.table(
        pd.DataFrame(
            audit_record.items(),
            columns=["Field", "Value"]
        )
    )


    # =====================================================
    # AI Decision Evaluation
    # =====================================================

    st.subheader("📏 AI Decision Evaluation")

    evaluation = evaluate_ai_decision(
        selected_payment,
        ai_result["action"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Expected Action",
            evaluation["expected_action"]
        )

    with col2:

        st.metric(
            "AI Action",
            evaluation["ai_action"]
        )

    with col3:

        if evaluation["correct"]:

            st.metric(
                "Decision Match",
                "100%"
            )

        else:

            st.metric(
                "Decision Match",
                "0%"
            )


    if evaluation["correct"]:

        st.success(
            "✅ AI decision matches the expected "
            "recovery strategy."
        )

    else:

        st.warning(
            "⚠️ AI decision differs from the expected "
            "recovery strategy. This mismatch is recorded "
            "rather than hidden."
        )


# =========================================================
# Batch Recovery Decisions
# =========================================================

st.divider()

st.header("📋 Recovery Decisions")

display_results = results_df[
    [
        "transaction_id",
        "failure_reason",
        "risk_level",
        "attempt_count",
        "action",
        "success",
        "recovered_amount"
    ]
].copy()

display_results = display_results.rename(
    columns={
        "transaction_id": "Transaction",
        "failure_reason": "Failure",
        "risk_level": "Risk",
        "attempt_count": "Attempts",
        "action": "Action",
        "success": "Recovered",
        "recovered_amount": "Recovered Amount"
    }
)

display_results["Recovered Amount"] = (
    display_results["Recovered Amount"]
    .apply(lambda x: f"₹{x:,.0f}")
)

st.dataframe(
    display_results,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# Batch Audit Trail
# =========================================================

st.header("🧾 Batch Audit Trail")

audit_df = results_df[
    [
        "transaction_id",
        "action",
        "safety_allowed",
        "result"
    ]
].copy()

audit_df = audit_df.rename(
    columns={
        "transaction_id": "Transaction",
        "action": "Final Action",
        "safety_allowed": "Safety Passed",
        "result": "Outcome"
    }
)

st.dataframe(
    audit_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# Architecture Note
# =========================================================

st.divider()

st.caption(
    "RecoverAI uses Gemini for AI decision support while "
    "deterministic controls enforce safety, stopping rules, "
    "simulation, evaluation, and measurement."
)