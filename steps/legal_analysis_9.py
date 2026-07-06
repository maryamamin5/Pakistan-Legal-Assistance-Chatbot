from core.extractor import extract_legal_analysis
from core.state import case_state, conversation_history
import json
import os
from datetime import datetime

def handle_step_9(user_message):
    # user_message is ignored here — step 9 just generates the report
    # no more questions to ask, just synthesize everything collected

    # Build facts dict from case_state — exclude internal tracking fields
    facts = {
        k: v for k, v in case_state.items()
        if k not in ["current_step"] and not k.endswith("_done")
    }

    # Generate the legal report from all collected facts
    report = extract_legal_analysis(facts)

    # Save session to disk
    os.makedirs("sessions", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"sessions/session_{timestamp}.json"

    session_data = {
        "case_facts": facts,
        "legal_report": report,
        "generated_at": timestamp
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

    # Build display text — one clean pass, no repetition
    laws = "\n".join(f"  • {law}" for law in report.get("relevant_pakistani_laws", []))
    rights = "\n".join(f"  • {item}" for item in report.get("rights_and_obligations", []))
    actions = "\n".join(f"  {i+1}. {action}" for i, action in enumerate(report.get("recommended_actions", [])))
    documents = "\n".join(f"  • {doc}" for doc in report.get("documents_needed", []))

    display_text = (
        f"\n{'=' * 60}\n"
        f"PAKISTAN LEGAL ASSISTANCE — CASE REPORT\n"
        f"{'=' * 60}\n\n"
        f"CASE SUMMARY:\n{report.get('case_summary', 'N/A')}\n\n"
        f"INCIDENT TYPE:\n{report.get('incident_type', 'N/A')}\n\n"
        f"RELEVANT PAKISTANI LAWS:\n{laws}\n\n"
        f"YOUR RIGHTS AND OBLIGATIONS:\n{rights}\n\n"
        f"RECOMMENDED ACTIONS:\n{actions}\n\n"
        f"DOCUMENTS YOU NEED:\n{documents}\n\n"
        f"DISCLAIMER:\n{report.get('legal_disclaimer', '')}\n"
        f"{'=' * 60}\n"
        f"(Session saved to {filepath})"
    )

    # Add to conversation history so it's part of the record
    conversation_history.append({"role": "assistant", "content": display_text})

    return display_text