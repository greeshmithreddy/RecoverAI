# RecoverAI

### AI-Powered Revenue Recovery Agent for Failed Payments

RecoverAI is an AI-assisted revenue recovery system that analyzes failed payment attempts, determines the most appropriate recovery strategy, and executes a controlled recovery workflow while minimizing unnecessary retries.

## Problem

Failed payments can represent significant lost revenue for online merchants.

A simple retry-everything approach can:

- Waste unnecessary payment attempts
- Frustrate customers
- Increase operational risk
- Repeat actions that are unlikely to succeed
- Provide poor visibility into why recovery decisions were made

RecoverAI addresses this by combining AI decision support with deterministic safety controls.

## Solution

RecoverAI follows a six-stage workflow:

**Detect → Diagnose → Decide → Safely Act → Measure → Audit**

For every failed payment, the system considers:

- Failure reason
- Number of previous attempts
- Historical payment success rate
- Customer tenure
- Payment amount
- Risk level

The AI recommends one of four actions:

- `RETRY` — attempt recovery for likely transient failures
- `NOTIFY` — prompt the customer to resolve the issue
- `ESCALATE` — send the case for human review
- `STOP` — safely stop further recovery attempts

## AI Decision Making

RecoverAI uses Gemini as an on-demand AI decision engine.

The AI produces:

- Diagnosis
- Recommended action
- Confidence score
- Reasoning for the recommendation

AI is used where contextual judgment is useful, while deterministic rules handle safety-critical controls.

## Safety Controls

AI recommendations never execute blindly.

The safety validator enforces:

- Allowed-action validation
- Maximum retry limits
- High-risk payment protection
- Safe escalation for unknown AI actions
- Mandatory stopping after repeated failures
- Audit logging of decisions and outcomes

If the AI produces an invalid or unsafe action, RecoverAI overrides it and safely escalates or stops the recovery workflow.

## Recovery Simulation

The project includes a synthetic payment recovery simulator.

The simulator models whether a selected recovery action succeeds based on controlled payment conditions.

This allows the system to measure:

- Recovery rate
- Revenue recovered
- Decision accuracy
- Safety compliance
- Average attempts
- Escalation rate

No real customer payments are processed.

## Architecture

```text
                 ┌──────────────────────┐
                 │   Merchant Dashboard │
                 │      Streamlit       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   Payment Dataset    │
                 │   Synthetic Data     │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    AI Decision       │
                 │       Gemini         │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   Safety Validator   │
                 │  Rules & Guardrails  │
                 └──────────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           RETRY          NOTIFY       ESCALATE
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Recovery Simulator   │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Results + Audit Log  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Merchant Dashboard   │
                 └──────────────────────┘