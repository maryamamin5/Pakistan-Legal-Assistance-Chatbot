import json
from utils.openai_client import client

def extract_legal_analysis(case_facts):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a Pakistani legal information assistant. You are NOT a lawyer
and must never give definitive legal advice or state a legal conclusion — only educational,
informational guidance based on general Pakistani law (e.g. Pakistan Penal Code, Motor Vehicles
Ordinance 1965, provincial traffic police rules, FIR procedures under the Code of Criminal Procedure).

You will be given structured facts about a road accident case. Based ONLY on these facts, produce
a legal guidance report.

Return ONLY a valid JSON object with EXACTLY this structure and these exact keys, nothing else —
no markdown, no backticks, no explanation before or after:

{
  "case_summary": "2-4 sentence plain-language summary of what happened, based only on the facts given",
  "incident_type": "road_accident",
  "relevant_pakistani_laws": ["law/section/procedure name", "..."],
  "rights_and_obligations": ["right or obligation of the parties, in plain language", "..."],
  "recommended_actions": ["practical next step the user can take", "..."],
  "documents_needed": ["document name", "..."],
  "legal_disclaimer": "This information is educational and not a substitute for professional legal advice."
}

Rules:
- Base case_summary strictly on the facts provided. Do not invent details not present in the facts.
- relevant_pakistani_laws: reference well-established Pakistani legal frameworks relevant to road accidents.
- rights_and_obligations: describe what each party may be entitled to or responsible for.
- recommended_actions: concrete practical steps based on what is still missing or pending in the facts.
- documents_needed: list documents relevant to the user's desired outcome and case facts.
- NEVER state definitively who was at fault or who will win any claim.
- ALWAYS include a recommendation to consult a licensed Pakistani lawyer in recommended_actions.
- Keep each list to 3-6 concise non-redundant items.
- Return raw JSON only."""
            },
            {
                "role": "user",
                "content": f"Case facts:\n{json.dumps(case_facts, indent=2)}"
            }
        ],
        max_tokens=800
    )

    raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "case_summary": "Unable to generate summary due to a formatting error.",
            "incident_type": case_facts.get("incident_type", "road_accident"),
            "relevant_pakistani_laws": [],
            "rights_and_obligations": [],
            "recommended_actions": ["Please consult a licensed Pakistani lawyer for guidance."],
            "documents_needed": [],
            "legal_disclaimer": "This information is educational and not a substitute for professional legal advice."
        }

    # Enforce required keys
    required_keys = [
        "case_summary", "incident_type", "relevant_pakistani_laws",
        "rights_and_obligations", "recommended_actions", "documents_needed",
        "legal_disclaimer"
    ]
    for key in required_keys:
        if key not in result:
            result[key] = [] if key.endswith("s") and key != "legal_disclaimer" else ""

    result["legal_disclaimer"] = "This information is educational and not a substitute for professional legal advice."

    return result