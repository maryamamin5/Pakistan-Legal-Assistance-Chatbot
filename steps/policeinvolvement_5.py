from core.guardrail import is_on_topic
from core.extractor import extract_police_details
from core.state import case_state, conversation_history
from utils.openai_client import client

def handle_step_5(user_message):

    if not is_on_topic(user_message, current_step=5):
        return "I can only assist with your legal matter. Let's continue — was the police informed about the incident?"

    # Guard: empty input or filler words — repeat the current pending question
    if not user_message.strip() or user_message.strip().lower() in [
        "ok", "okay", "sure", "thanks", "thank you", "welcome", "got it", "fine", "alright"
    ]:
        return _repeat_current_question()

    # Detect simple yes/no from the user's message
    simple = _detect_yes_no(user_message)

    # Directly map yes/no to whichever field is currently pending
    # This bypasses the stateless extractor for sequential yes/no questions
    if not case_state["police_informed"]:
        if simple:
            case_state["police_informed"] = simple
        else:
            # Not a yes/no — use extractor for richer answers like "we called the police"
            extracted = extract_police_details(user_message)
            if extracted["police_informed"] in ["yes", "no"]:
                case_state["police_informed"] = extracted["police_informed"]

    elif not case_state["fir_registered"]:
        if simple:
            case_state["fir_registered"] = simple
        else:
            extracted = extract_police_details(user_message)
            if extracted["fir_registered"] in ["yes", "no"]:
                case_state["fir_registered"] = extracted["fir_registered"]

    elif not case_state["challan_issued"]:
        if simple:
            case_state["challan_issued"] = simple
        else:
            extracted = extract_police_details(user_message)
            if extracted["challan_issued"] in ["yes", "no"]:
                case_state["challan_issued"] = extracted["challan_issued"]

    elif not case_state["arrests_made"]:
        if simple:
            case_state["arrests_made"] = simple
        else:
            extracted = extract_police_details(user_message)
            if extracted["arrests_made"] in ["yes", "no"]:
                case_state["arrests_made"] = extracted["arrests_made"]

    # Add to history
    conversation_history.append({"role": "user", "content": user_message})

    # Police NOT informed — skip remaining fields, go to step 6
    if case_state["police_informed"] == "no":
        case_state["fir_registered"] = "no"
        case_state["challan_issued"] = "no"
        case_state["arrests_made"] = "no"
        case_state["current_step"] = 6
        bot_reply = _ask_strictly(
            "Police were not informed. Acknowledge in one sentence. "
            "Then ask who the user believes was responsible and what caused the accident — "
            "overspeeding, signal violation, distracted driving, etc. ONE question only."
        )
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # Still missing fields — ask for next pending one
    if not case_state["police_informed"]:
        bot_reply = _ask_strictly("Ask: was the police informed about this incident? Yes or no only.")
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["fir_registered"]:
        bot_reply = _ask_strictly("Ask: was an FIR registered at the police station? Yes or no only.")
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["challan_issued"]:
        bot_reply = _ask_strictly("Ask: was a traffic challan issued by the police? Yes or no only.")
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    if not case_state["arrests_made"]:
        bot_reply = _ask_strictly("Ask: were any arrests made in connection with this incident? Yes or no only.")
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # All fields filled — advance to step 6
    case_state["step5_done"] = True 
    case_state["current_step"] = 6

    police_summary = (
        f"police informed: {case_state['police_informed']}, "
        f"FIR registered: {case_state['fir_registered']}, "
        f"challan issued: {case_state['challan_issued']}, "
        f"arrests made: {case_state['arrests_made']}"
    )

    bot_reply = _ask_strictly(
        f"""Police details complete: {police_summary}.
        Acknowledge in ONE sentence.
        Then ask ONLY: who does the user believe was responsible for this accident,
        and what caused it — overspeeding, signal violation, distracted driving, etc.
        ONE question only. Do NOT ask about evidence or outcomes yet."""
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply


def _detect_yes_no(message):
    msg = message.strip().lower()
    
    # Exact single-word matches — unambiguous
    yes_exact = ["yes", "yeah", "yep", "yup", "correct", "affirmative"]
    no_exact = ["no", "nope", "nah", "none", "never"]
    
    if msg in yes_exact:
        return "yes"
    if msg in no_exact:
        return "no"
    
    # Phrase-based for longer messages
    yes_phrases = ["fir registered", "fir filed", "case registered",
                   "they did", "we did", "it was registered", "was filed",
                   "police came", "arrest was made", "someone was arrested",
                   "challan was issued"]
    no_phrases = ["no fir", "not registered", "didn't file", "no arrest",
                  "no challan", "was not", "did not", "wasn't"]
    
    if any(phrase in msg for phrase in yes_phrases):
        return "yes"
    if any(phrase in msg for phrase in no_phrases):
        return "no"
    
    return None



def _repeat_current_question():
    """Returns the question for whichever field is currently pending."""
    if not case_state["police_informed"]:
        return "Was the police informed about the incident? Please answer yes or no."
    if not case_state["fir_registered"]:
        return "Was an FIR registered at the police station? Please answer yes or no."
    if not case_state["challan_issued"]:
        return "Was a traffic challan issued? Please answer yes or no."
    if not case_state["arrests_made"]:
        return "Were any arrests made? Please answer yes or no."
    return "Please continue."


def _ask_strictly(instruction):
    # Build a state summary to inject into every GPT call
    # This prevents GPT from hallucinating or contradicting what's already stored
    state_context = f"""
CURRENT VERIFIED CASE STATE (these are facts already confirmed by the user — never contradict them):
- Incident type: {case_state['incident_type']}
- Date: {case_state['date']}
- Location: {case_state['city']}, {case_state['province']}
- Road type: {case_state['road_type']}
- Vehicles involved: {case_state['vehicles_involved']}
- Injuries: {case_state['injuries']}
- Injury severity: {case_state['injury_severity']}
- Medical treatment: {case_state['medical_treatment']}
- Vehicle damage: {case_state['vehicle_damage']}
- Property damage: {case_state['property_damage']}
- Financial loss: {case_state['financial_loss']}
- Police informed: {case_state['police_informed']}
- FIR registered: {case_state['fir_registered']}
- Challan issued: {case_state['challan_issued']}
- Arrests made: {case_state['arrests_made']}
- Fault party: {case_state['fault_party']}
- Overspeeding: {case_state['overspeeding']}
- Signal violation: {case_state['signal_violation']}
- License status: {case_state['license_status']}
- DUI: {case_state['dui']}
- Evidence: {case_state['evidence']}
- Desired outcome: {case_state['desired_outcome']}

COMPLETED STEPS: {[k for k, v in case_state.items() if k.endswith('_done') and v is True]}
CURRENT STEP: {case_state['current_step']}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""You are a Pakistan legal intake assistant.

{state_context}

STRICT RULES:
1. Your ONLY job: {instruction}
2. NEVER contradict the verified case state above — if injuries are confirmed, never say "no injuries reported"
3. Ask ONE question only. Stop immediately after.
4. Do NOT say 'Thank you for confirming' or any preamble before the question.
5. Do NOT give legal advice or conclusions.
6. Start directly with the question or brief acknowledgment as instructed.
7. Keep response under 2 sentences."""
            }
        ] + conversation_history,
        max_tokens=120
    )
    return response.choices[0].message.content.strip()