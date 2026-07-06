from core.guardrail import is_on_topic
from core.extractor import extract_evidence_details
from core.state import case_state, conversation_history
from utils.openai_client import client

FILLER_WORDS = ["ok", "okay", "sure", "thanks", "thank you", "welcome", "got it", "fine"]

def handle_step_7(user_message):

    if not is_on_topic(user_message, current_step=7):
        return "I can only assist with your legal matter. Do you have any evidence related to the incident?"

    if not user_message.strip() or user_message.strip().lower() in FILLER_WORDS:
        return "Do you have any evidence — photos, videos, witness statements, police report, medical reports, or insurance documents? List what you have or say 'none'."

    # Extract evidence from message
    extracted = extract_evidence_details(user_message)

    msg = user_message.strip().lower()

    # Store evidence list
    if extracted.get("evidence"):
        case_state["evidence"] = extracted["evidence"]
    elif "none" in msg or "nothing" in msg or "no evidence" in msg or "don't have" in msg:
        case_state["evidence"] = []
    elif extracted.get("has_evidence") == "no":
        case_state["evidence"] = []

    conversation_history.append({"role": "user", "content": user_message})

    # If evidence state still unknown — ask again
    if extracted.get("has_evidence") is None and case_state["evidence"] == []:
        # Check if user gave any response at all
        if not extracted.get("evidence") and "none" not in msg and "nothing" not in msg:
            bot_reply = "Do you have any evidence related to the incident — such as photos, videos, witness statements, police report, medical reports, or insurance documents? Please list what you have or say 'none'."
            conversation_history.append({"role": "assistant", "content": bot_reply})
            return bot_reply

    # Evidence state is known — advance to step 8
    case_state["step_7_done"] = True
    case_state["current_step"] = 8

    if case_state["evidence"]:
        evidence_text = ", ".join(case_state["evidence"])
        evidence_summary = f"evidence available: {evidence_text}"
    else:
        evidence_summary = "no evidence available"

    bot_reply = (
        f"Got it — {evidence_summary}. "
        f"What outcome are you hoping for from this situation? "
        f"Choose one or more: compensation, insurance claim, "
        f"criminal action against the other party, FIR registration, "
        f"court proceedings, or out-of-court settlement."
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply