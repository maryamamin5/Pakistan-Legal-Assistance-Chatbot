from core.guardrail import is_on_topic
from core.extractor import extract_desired_outcome
from core.state import case_state, conversation_history
from utils.openai_client import client

FILLER_WORDS = ["ok", "okay", "sure", "thanks", "thank you", "welcome", "got it", "fine", "alright"]

def handle_step_8(user_message):

    # Guard 1 — off-topic
    if not is_on_topic(user_message, current_step=8):
        return "I can only assist with your legal matter. " + _repeat_current_question()

    # Guard 2 — filler or empty
    if not user_message.strip() or user_message.strip().lower() in FILLER_WORDS:
        return _repeat_current_question()

    # Extract desired outcome from user's message
    extracted = extract_desired_outcome(user_message)

    # Store only if confident — reject "unclear" and None
    if extracted.get("desired_outcome") and extracted["desired_outcome"] != "unclear":
        case_state["desired_outcome"] = extracted["desired_outcome"]

    conversation_history.append({"role": "user", "content": user_message})

    # Outcome still unknown — ask again with hardcoded string
    if not case_state["desired_outcome"]:
        bot_reply = (
            "What outcome are you hoping to achieve from this situation? "
            "Options: compensation, insurance claim, criminal action against the other party, "
            "FIR registration, court proceedings, or out-of-court settlement. "
            "You can choose more than one."
        )
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # Outcome confirmed — mark step 8 done and advance to step 9
    case_state["step_8_done"] = True
    case_state["current_step"] = 9

    bot_reply = (
        f"Understood — desired outcome: {case_state['desired_outcome'].replace('_', ' ')}. "
        f"I now have all the information needed to prepare your legal guidance report. "
        f"Type anything when you are ready to see it."
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply


def _repeat_current_question():
    if not case_state["desired_outcome"]:
        return (
            "What outcome are you hoping for — compensation, insurance claim, "
            "criminal action, FIR registration, court proceedings, or settlement?"
        )
    return "Please continue."