from core.guardrail import is_on_topic
from core.extractor import extract_liability_details
from core.state import case_state, conversation_history
from utils.openai_client import client

FILLER_WORDS = ["ok", "okay", "sure", "thanks", "thank you", "welcome", "got it", "fine", "alright"]

def handle_step_6(user_message):

    # Guard 1 — off-topic
    if not is_on_topic(user_message, current_step=6):
        return "I can only assist with your legal matter. " + _repeat_current_question()

    # Guard 2 — filler or empty
    if not user_message.strip() or user_message.strip().lower() in FILLER_WORDS:
        return _repeat_current_question()

    # Detect simple yes/no directly without extractor
    simple = _detect_yes_no(user_message)

    # Priority queue — fill only the FIRST missing field from this message
    if not case_state["fault_party"]:
        msg = user_message.strip().lower()

        # Direct keyword mapping first — catches common phrases the extractor misses
        if any(w in msg for w in ["myself", "i was", "my fault", "i caused", "i did", "yourself"]):
            case_state["fault_party"] = "user"
        elif any(w in msg for w in ["other party", "other driver", "other person",
                                     "he was", "she was", "they were",
                                     "their fault", "other car", "the other"]):
            case_state["fault_party"] = "other_party"
        elif any(w in msg for w in ["both", "both of us", "shared", "mutual"]):
            case_state["fault_party"] = "both"
        else:
            # Fallback to extractor for richer descriptions
            extracted = extract_liability_details(user_message)
            if extracted.get("fault_party") in ["user", "other_party", "both"]:
                case_state["fault_party"] = extracted["fault_party"]

    elif not case_state["overspeeding"]:
        if simple:
            case_state["overspeeding"] = simple

    elif not case_state["signal_violation"]:
        if simple:
            case_state["signal_violation"] = simple

    elif not case_state["license_status"]:
        msg = user_message.strip().lower()
        if any(w in msg for w in ["no license", "without license", "without a license",
                                   "without a valid", "unlicensed", "no valid license"]):
            case_state["license_status"] = "no_license"
        elif "expired" in msg:
            case_state["license_status"] = "expired"
        elif simple == "no":
            case_state["license_status"] = "valid"
        elif any(w in msg for w in ["valid", "had license", "licensed", "with license"]) and "without" not in msg:
            case_state["license_status"] = "valid"

    elif not case_state["dui"]:
        if simple:
            case_state["dui"] = simple

    # Add to history
    conversation_history.append({"role": "user", "content": user_message})

    # Ask for next missing field — all hardcoded strings
    if not case_state["fault_party"]:
        bot_reply = "Who do you believe was responsible for this accident — yourself, the other party, or both? Please briefly describe what caused it."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["overspeeding"]:
        bot_reply = "Was overspeeding a factor in this accident? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["signal_violation"]:
        bot_reply = "Was a traffic signal or red light violated? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["license_status"]:
        bot_reply = "Was the driver who caused the accident driving with a valid license, without a license, or with an expired license?"
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["dui"]:
        bot_reply = "Was there any indication that the driver was under the influence of alcohol or drugs? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # All fields confirmed — mark done and advance to step 7
    case_state["step_6_done"] = True
    case_state["current_step"] = 7

    bot_reply = (
        f"Noted — fault: {case_state['fault_party']}, "
        f"overspeeding: {case_state['overspeeding']}, "
        f"signal violation: {case_state['signal_violation']}, "
        f"license: {case_state['license_status']}, "
        f"DUI: {case_state['dui']}. "
        f"Do you have any evidence related to this incident? "
        f"For example: photos, videos, witness statements, police report, "
        f"medical reports, or insurance documents. List what you have or say 'none'."
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply


def _detect_yes_no(message):
    msg = message.strip().lower()

    # Exact single-word matches — unambiguous
    yes_exact = ["yes", "yeah", "yep", "yup", "correct", "affirmative"]
    no_exact = ["no", "nope", "nah", "never"]

    if msg in yes_exact:
        return "yes"
    if msg in no_exact:
        return "no"

    # Phrase-based for longer messages
    yes_phrases = ["it was", "there was", "they did", "he did", "she did", "was done"]
    no_phrases = ["was not", "did not", "wasn't", "didn't", "no sign", "not done"]

    if any(p in msg for p in yes_phrases):
        return "yes"
    if any(p in msg for p in no_phrases):
        return "no"

    return None


def _repeat_current_question():
    if not case_state["fault_party"]:
        return "Who do you believe was responsible — yourself, the other party, or both?"
    if not case_state["overspeeding"]:
        return "Was overspeeding a factor? Yes or no."
    if not case_state["signal_violation"]:
        return "Was a traffic signal violated? Yes or no."
    if not case_state["license_status"]:
        return "Was the driver licensed, unlicensed, or had an expired license?"
    if not case_state["dui"]:
        return "Was the driver under the influence of alcohol or drugs? Yes or no."
    return "Please continue."