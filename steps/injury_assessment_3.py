from core.guardrail import is_on_topic
from core.extractor import extract_injury_details
from core.state import case_state, conversation_history
from utils.openai_client import client

FILLER_WORDS = ["welcome", "okay", "ok", "sure", "alright", "thanks", "thank you", "got it", "fine"]

def _current_missing_question_step3():
    if not case_state["injuries"]:
        return "Were there any injuries in the incident? Please answer yes or no."
    if not case_state["injury_severity"]:
        return "How serious were the injuries — minor, serious, or fatal?"
    if not case_state["medical_treatment"]:
        return "Was medical treatment required — did anyone visit a doctor or hospital? Yes or no."
    return "Please continue with your response."

def handle_step_3(user_message):
    # Guard 1 — off-topic
    if not is_on_topic(user_message, current_step=3):
        return "I can only assist with your legal matter. " + _current_missing_question_step3()

    # Guard 2 — filler words
    if user_message.strip().lower() in FILLER_WORDS:
        return _current_missing_question_step3()

    # Guard 3 — empty input
    if not user_message.strip():
        return _current_missing_question_step3()

    # Extract structured data
    extracted = extract_injury_details(user_message)


    # Store only confident extractions
    # Store only confident extractions — but NEVER overwrite an already-confirmed field
    if extracted["injuries"] in ["yes", "no"] and not case_state["injuries"]:
        case_state["injuries"] = extracted["injuries"]
    if extracted["injury_severity"] in ["minor", "serious", "fatal"] and not case_state["injury_severity"]:
        case_state["injury_severity"] = extracted["injury_severity"]
    if extracted["medical_treatment"] in ["yes", "no"] and not case_state["medical_treatment"]:
        case_state["medical_treatment"] = extracted["medical_treatment"]

    # Enforce logical consistency
    if case_state["injury_severity"] and not case_state["injuries"]:
        case_state["injuries"] = "yes"
    if case_state["medical_treatment"] == "yes" and not case_state["injuries"]:
        case_state["injuries"] = "yes"


    conversation_history.append({"role": "user", "content": user_message})

    # ── SUB-STEP A — do we know if injuries happened? ──
    if not case_state["injuries"]:
        bot_reply = "Were there any injuries in the incident? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # ── SUB-STEP A2 — injuries confirmed but severity unknown ──
    if case_state["injuries"] == "yes" and not case_state["injury_severity"]:
        bot_reply = "How serious were the injuries — minor, serious, or fatal?"
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # ── SUB-STEP B — severity known, was medical treatment needed? ──
    if case_state["injuries"] == "yes" and not case_state["medical_treatment"]:
        bot_reply = "Was medical treatment required — did anyone visit a doctor or hospital? Yes or no."
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # ── SAFETY CHECK — never advance if anything still missing ──
    if not case_state["injuries"] or (
        case_state["injuries"] == "yes" and (
            not case_state["injury_severity"] or
            not case_state["medical_treatment"]
        )
    ):
        bot_reply = _current_missing_question_step3()
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return bot_reply

    # ── ALL FIELDS CONFIRMED — build summary and advance ──

    # Final consistency enforcement
    if case_state["injury_severity"] and not case_state["injuries"]:
        case_state["injuries"] = "yes"

    # Build summary from state — never from GPT
    if case_state["injuries"] == "no":
        injury_summary = "no injuries were reported"
    elif case_state["injuries"] == "yes" and case_state["injury_severity"]:
        treatment = (
            "medical treatment was required"
            if case_state["medical_treatment"] == "yes"
            else "no medical treatment was needed"
        )
        injury_summary = f"{case_state['injury_severity']} injuries occurred and {treatment}"
    else:
        injury_summary = "injuries were reported"

    case_state["step_3_done"] = True
    case_state["current_step"] = 4

    bot_reply = (
        f"Injury details complete: {injury_summary}. "
        f"How badly was the vehicle damaged? "
        f"Choose one: minor damage (scratches or dents), "
        f"moderate damage (significant but still drivable), "
        f"or total loss (completely destroyed)."
    )
    conversation_history.append({"role": "assistant", "content": bot_reply})
    return bot_reply

# _ask_strictly stays here exactly as before — unchanged
def _ask_strictly(instruction):
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
2. NEVER contradict the verified case state above
3. Ask ONE question only. Stop immediately after.
4. Do NOT say 'Thank you for confirming' or any preamble.
5. Do NOT give legal advice or conclusions.
6. Start directly with the question or acknowledgment.
7. Keep response under 2 sentences."""
            }
        ] + conversation_history,
        max_tokens=120
    )
    return response.choices[0].message.content.strip()