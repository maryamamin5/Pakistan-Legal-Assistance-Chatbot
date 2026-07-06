from core.guardrail import is_on_topic
from core.extractor import extract_property_damage
from core.state import case_state, conversation_history
from utils.openai_client import client

FILLER_WORDS = ["welcome", "okay", "ok", "sure", "alright", "thanks", "thank you", "got it", "fine"]

def _current_missing_question_step4():
    if not case_state["vehicle_damage"]:
        return "How badly was the vehicle damaged — minor, moderate, or total loss?"
    if not case_state["property_damage"]:
        return "Was any public or private property also damaged? Yes or no."
    if not case_state["financial_loss"]:
        return "What is the estimated financial loss? An approximate figure is fine."
    return "Please continue with your response."

def handle_step_4(user_message):
    if not is_on_topic(user_message, current_step=4):
        return "I can only assist with your legal matter. " + _current_missing_question_step4()

    if user_message.strip().lower() in FILLER_WORDS:
        return _current_missing_question_step4()

    if not user_message.strip():
        return _current_missing_question_step4()

    extracted = extract_property_damage(user_message)

    if extracted["vehicle_damage"] in ["minor", "moderate", "total_loss"]:
        case_state["vehicle_damage"] = extracted["vehicle_damage"]
    if extracted["property_damage"] in ["yes", "no"]:
        case_state["property_damage"] = extracted["property_damage"]
    if extracted["financial_loss"] and extracted["financial_loss"] not in ["null", "yes", "no"]:
        case_state["financial_loss"] = extracted["financial_loss"]

    conversation_history.append({"role": "user", "content": user_message})

    if not case_state["vehicle_damage"]:
        bot_reply = "How badly was the vehicle damaged? Choose one: minor damage (scratches or dents), moderate damage (significant but still drivable), or total loss (completely destroyed)."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply
    
    if not case_state["property_damage"]:
        bot_reply = "Was any public or private property also damaged — such as road signs, dividers, boundary walls, or shops? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply
    
    if not case_state["financial_loss"]:
        bot_reply = "What is the estimated financial loss from this incident? Give an approximate amount in rupees, or say 'not sure' if you are unsure."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    case_state["step_4_done"] = True
    case_state["current_step"] = 5

    bot_reply = (
        f"Got it — vehicle damage: {case_state['vehicle_damage'].replace('_', ' ')}, "
        f"property damage: {case_state['property_damage']}, "
        f"estimated loss: {case_state['financial_loss']}. "
        f"Was the police informed about this incident? Yes or no."
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply