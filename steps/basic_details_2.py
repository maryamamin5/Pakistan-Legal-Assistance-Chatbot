from core.guardrail import is_on_topic
from core.extractor import extract_basic_details
from core.state import case_state, conversation_history
from utils.openai_client import client

def handle_step_2(user_message):

    # 1. Guardrail
    if not is_on_topic(user_message, current_step=2):
        return "I can only assist with your legal matter. " + _repeat_current_question()

    # 2. Empty input or filler — repeat current pending question
    if not user_message.strip() or user_message.strip().lower() in [
        "ok", "okay", "sure", "thanks", "thank you", "welcome", "got it", "fine", "yes", "no"
    ]:
        return _repeat_current_question()

    # 3. Extract whatever fields are present in the message
    extracted = extract_basic_details(user_message)

    # 4. Store only what was confidently extracted — one field at a time
    # Priority: fill whichever field is currently missing
    if not case_state["date"] and extracted.get("date"):
        case_state["date"] = extracted["date"]

    if not case_state["city"] and extracted.get("city"):
        case_state["city"] = extracted["city"]

    if not case_state["province"] and extracted.get("province"):
        case_state["province"] = extracted["province"]

    if not case_state["road_type"] and extracted.get("road_type"):
        case_state["road_type"] = extracted["road_type"]

    if not case_state["vehicles_involved"] and extracted.get("vehicles_involved"):
        case_state["vehicles_involved"] = extracted["vehicles_involved"]

    # 5. Add to history
    conversation_history.append({"role": "user", "content": user_message})

    # 6. Check what is still missing and ask ONLY for that — one field at a time
    if not case_state["date"]:
        reply = "What was the date of the incident?"
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

    if not case_state["city"] or not case_state["province"]:
        reply = "Which city and province in Pakistan did this occur in?"
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

    if not case_state["road_type"]:
        reply = "What type of road was it — a highway, city street, rural road, or motorway?"
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

    if not case_state["vehicles_involved"]:
        reply = "How many vehicles were involved in the incident?"
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

    # 7. All 4 fields confirmed — mark step 2 done and advance
    case_state["step_2_done"] = True
    case_state["current_step"] = 3

    # Build confirmed summary from actual state — not from GPT
    summary = (
        f"Got it — an incident on {case_state['date']} "
        f"in {case_state['city']}, {case_state['province']}, "
        f"on a {case_state['road_type'].replace('_', ' ')}, "  # ← add this
        f"involving {case_state['vehicles_involved']} vehicle(s). "
        f"Were there any injuries? If yes, how serious were they — minor, serious, or fatal?"
    )

    conversation_history.append({"role": "assistant", "content": summary})
    return summary


def _repeat_current_question():
    """Returns the hardcoded question for whichever field is currently missing."""
    if not case_state["date"]:
        return "What was the date of the incident?"
    if not case_state["city"] or not case_state["province"]:
        return "Which city and province in Pakistan did this occur in?"
    if not case_state["road_type"]:
        return "What type of road was it — highway, city street, rural road, or motorway?"
    if not case_state["vehicles_involved"]:
        return "How many vehicles were involved?"
    return "Please continue with the incident details."