from steps.incidenttype_1 import handle_step_1
from steps.basic_details_2 import handle_step_2
from steps.injury_assessment_3 import handle_step_3
from steps.propertydamage_4 import handle_step_4
from steps.policeinvolvement_5 import handle_step_5
from steps.liability_assessment_6 import handle_step_6
from steps.evidence_collection_7 import handle_step_7
from steps.desired_outcome_8 import handle_step_8
from steps.legal_analysis_9 import handle_step_9
from core.state import case_state, conversation_history

print("Bot: Assalam o Alaikum! I am your Pakistan Legal Assistance chatbot.")
print("Bot: Please describe your legal issue to get started.\n")

while True:
    user_input = input("You: ")

    if case_state["current_step"] == 1:
        response = handle_step_1(user_input)
    elif case_state["current_step"] == 2:
        response = handle_step_2(user_input)
    elif case_state["current_step"] == 3:
        response = handle_step_3(user_input)
    elif case_state["current_step"] == 4:
        response = handle_step_4(user_input)
    elif case_state["current_step"] == 5:
        response = handle_step_5(user_input)
    elif case_state["current_step"] == 6:
        response = handle_step_6(user_input)
    elif case_state["current_step"] == 7:
        response = handle_step_7(user_input)
    elif case_state["current_step"] == 8:
        response = handle_step_8(user_input)
    elif case_state["current_step"] == 9:
        response = handle_step_9(user_input)
        print(f"\nBot: {response}\n")
        print("Conversation complete. Thank you.")
        break
    else:
        response = f"[Step {case_state['current_step']} not implemented yet]"

    print(f"\nBot: {response}\n")
    print(f"DEBUG: step={case_state['current_step']} | history_length={len(conversation_history)}")