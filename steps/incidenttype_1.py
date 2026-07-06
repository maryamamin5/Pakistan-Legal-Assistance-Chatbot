from core.guardrail import is_on_topic
from core.extractor import extract_incident_type
from core.state import case_state, conversation_history
from utils.openai_client import client

def handle_step_1(user_message):
    if not is_on_topic(user_message,current_step=1):
        return "I can only assist with legal matters in Pakistan. Please describe your legal issue to begin."
    incident_type = extract_incident_type(user_message)

    if incident_type == "unclear":
        return (
            "I'd like to help you with your legal matter. "
            "Could you describe your situation a bit more clearly? "
            "For example: road accident, property dispute, employment issue, theft, etc."
        )

    case_state["incident_type"] = incident_type
    case_state["current_step"] = 2

    # 5. Add user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # 6. Generate natural acknowledgment + step 2 question
    system_prompt = f"""You are a warm, professional Pakistan legal intake assistant. You are NOT a lawyer.
You are gathering information step by step before giving educational legal guidance.
Do NOT give any legal conclusions or advice yet.

The user has reported a {incident_type.replace('_', ' ')}.
Briefly acknowledge what they said in one sentence.
Then ask them for:
- The date the incident occurred
- The city and province in Pakistan where it happened
- The type of road (highway, city street, rural road, etc.)
- How many vehicles were involved

Ask all of this as one natural flowing paragraph. Do not use bullet points or numbered lists."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt}
        ] + conversation_history,
        max_tokens=200
    )

    bot_reply = response.choices[0].message.content.strip()
    conversation_history.append({"role": "assistant", "content": bot_reply})

    return bot_reply