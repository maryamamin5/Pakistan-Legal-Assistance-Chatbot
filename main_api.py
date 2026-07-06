from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from core.state import case_state, conversation_history
from steps.incidenttype_1 import handle_step_1
from steps.basic_details_2 import handle_step_2
from steps.injury_assessment_3 import handle_step_3
from steps.propertydamage_4 import handle_step_4
from steps.policeinvolvement_5 import handle_step_5
from steps.liability_assessment_6 import handle_step_6
from steps.evidence_collection_7 import handle_step_7
from steps.desired_outcome_8 import handle_step_8
from steps.legal_analysis_9 import handle_step_9

app = FastAPI()

# Serve static files (your HTML/CSS/JS)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request model — what the browser sends
class ChatRequest(BaseModel):
    message: str

# Response model — what we send back
class ChatResponse(BaseModel):
    reply: str
    step: int
    done: bool

@app.get("/")
def serve_ui():
    """Serve the chat interface when browser opens the URL"""
    return FileResponse("static/index.html")

@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """
    Main endpoint — receives user message, routes to correct step handler,
    returns bot reply
    """
    user_message = request.message.strip()
    current_step = case_state["current_step"]

    if current_step == 1:
        reply = handle_step_1(user_message)
    elif current_step == 2:
        reply = handle_step_2(user_message)
    elif current_step == 3:
        reply = handle_step_3(user_message)
    elif current_step == 4:
        reply = handle_step_4(user_message)
    elif current_step == 5:
        reply = handle_step_5(user_message)
    elif current_step == 6:
        reply = handle_step_6(user_message)
    elif current_step == 7:
        reply = handle_step_7(user_message)
    elif current_step == 8:
        reply = handle_step_8(user_message)
    elif current_step == 9:
        reply = handle_step_9(user_message)
    else:
        reply = "Conversation complete."

    return ChatResponse(
        reply=reply,
        step=case_state["current_step"],
        done=case_state["current_step"] > 9
    )

@app.post("/reset")
def reset():
    """Reset the conversation state for a new session"""
    case_state.clear()
    case_state.update({
        "current_step": 1,
        "step_1_done": False,
        "step_2_done": False,
        "step_3_done": False,
        "step_4_done": False,
        "step_5_done": False,
        "step_6_done": False,
        "step_7_done": False,
        "step_8_done": False,
        "incident_type": None,
        "date": None,
        "city": None,
        "province": None,
        "road_type": None,
        "vehicles_involved": None,
        "injuries": None,
        "injury_severity": None,
        "medical_treatment": None,
        "vehicle_damage": None,
        "property_damage": None,
        "financial_loss": None,
        "police_informed": None,
        "fir_registered": None,
        "challan_issued": None,
        "arrests_made": None,
        "fault_party": None,
        "overspeeding": None,
        "signal_violation": None,
        "license_status": None,
        "dui": None,
        "evidence": [],
        "desired_outcome": None
    })
    conversation_history.clear()
    return {"status": "reset successful"}