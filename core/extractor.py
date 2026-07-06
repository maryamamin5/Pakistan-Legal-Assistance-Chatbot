from utils.openai_client import client
import json
from utils.openai_client import client
def extract_incident_type(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract the type of legal issue from a user's message.
Return ONLY one of these exact values, nothing else, no explanation:

road_accident
property_dispute
employment_issue
domestic_matter
consumer_complaint
cybercrime
theft_robbery
unclear

If you cannot confidently identify the issue type, return: unclear"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=10
    )
    return response.choices[0].message.content.strip().lower()

def extract_basic_details(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract basic incident details from a user's message.
Return ONLY a valid JSON object with exactly these 4 keys, nothing else:

{
  "date": "the date mentioned or null if not mentioned",
  "city": "the city mentioned or null if not mentioned",
  "province": "the province mentioned or null if not mentioned",
  "road_type": "highway / city_street / motorway / unknown or null if not mentioned",
  "vehicles_involved": "the number or description mentioned — accept exact numbers like '2' OR words like 'many', 'several', 'a lot', 'multiple'. Set null only if completely not mentioned."
}

Rules:
- If a value is not mentioned at all, set it to null
- For date, accept any format the user gives (yesterday, 3 june, last week)
- For province, infer from city if obvious (Lahore = Punjab, Karachi = Sindh)
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=150
    )

    import json
    raw = response.choices[0].message.content.strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "date": None,
            "city": None,
            "province": None,
            "road_type": None,
            "vehicles_involved": None
        }
    
def extract_injury_details(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content":"""You extract injury information from a user's message.
Return ONLY a valid JSON object with exactly these keys, nothing else:

{
  "injuries": "yes / no / unclear",
  "injury_severity": "minor / serious / fatal / null",
  "medical_treatment": "yes / no / unclear / null"
}

Rules:
- injuries: 
    Set YES if user mentions any injury, pain, hurt, wound, or severity words (serious, minor, fatal, major, severe, slight)
    Describing severity IMPLIES injuries=yes — do not leave it null if severity is mentioned
    Set NO only if user explicitly says no one was hurt
    Set unclear only if truly ambiguous
- injury_severity:
    minor = small injuries, bruises, cuts, light, slight, not serious
    serious = major, severe, significant, bad, broken bones, very serious, hospitalization needed
    fatal = death occurred, someone died, killed
    Map synonyms confidently. "very serious" = serious. "major" = serious. "slight" = minor
    Set null only if injuries=no
- medical_treatment: ONLY set yes or no if the user EXPLICITLY mentions medical care
  yes = user explicitly says: hospital, doctor, clinic, treatment, ambulance, admitted, checkup, ward, surgery
  no = user explicitly says: no hospital, no doctor, no treatment, didn't go, not needed, fine without treatment
  null = user said NOTHING about medical care — this is the DEFAULT
  CRITICAL: "serious" alone = null. "fatal" alone = null. "minor" alone = null.
  CRITICAL: Injury severity words are NOT medical treatment words — never connect them
  CRITICAL: Silence about treatment = null, NOT no. When in doubt always return null.
  "serious injuries" = medical_treatment: null (severity mentioned, treatment not mentioned)
  "serious injuries, went to hospital" = medical_treatment: yes
  "minor injuries, no doctor needed" = medical_treatment: no
  CRITICAL: If injury_severity is set to anything other than null, injuries MUST be "yes"
  Never return injury_severity=serious with injuries=null — that is contradictory
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=100
    )

    import json
    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "injuries": "unclear",
            "injury_severity": None,
            "medical_treatment": None
        }

    
def extract_property_damage(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """you extract property damage details from a user's messag
Return ONLY a valid JSON object with exactly these keys, nothing else:
{
    "vehicle_damage": "minor / moderate / total_loss / null",
    "property_damage": "yes / no / unclear / null",
     "financial_loss": "the amount or description mentioned, or null if not mentioned"

}
Rules:
- vehicle_damage: how badly was the vehicle damaged? minor (scratches, small dents),      
moderate (larger dents, broken parts), total_loss (vehicle is a total loss). Set null if not mentioned.
- property_damage: was any public or private property damaged? yes, no, unclear, or null if not mentioned.
- financial_loss:ONLY extract if the user explicitly mentions an amount, figure, or money
  Accept: "50,000 rupees", "1 lakh", "around 2 lakh", "not sure", "don't know the amount"
  Do NOT set this from "yes" alone — "yes" is not a financial figure
  Do NOT infer financial loss from property damage confirmation
  Set null if no amount or explicit "not sure" is mentioned
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=100
    )
    import json
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "vehicle_damage": None,
            "property_damage": None,
            "financial_loss": None
        }
def extract_police_details(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract police involvement details from a user's message.
Return ONLY a valid JSON object with exactly these keys, nothing else:

{
  "police_informed": "yes / no / null",
  "fir_registered": "yes / no / null",
  "challan_issued": "yes / no / null",
  "arrests_made": "yes / no / null"
}

Rules:
- police_informed: did the user call or inform police? yes, no, or null if not mentioned
- fir_registered: was a First Information Report filed? yes, no, or null if not mentioned
  Synonyms for yes: FIR filed, case registered, report made, lodged a complaint
  Synonyms for no: no FIR, didn't file, not registered
- challan_issued: was a traffic challan or ticket given by police? yes, no, or null
- arrests_made: was anyone arrested or detained? yes, no, or null
  Synonyms for yes: arrested, detained, taken into custody, caught
- If the user says police were NOT informed, set fir_registered, challan_issued, arrests_made all to "no" automatically
-CRITICAL: Only extract a field if it is EXPLICITLY mentioned in the message
  "yes" alone = only police_informed:yes, everything else stays null
  Each field needs its own explicit mention — never infer FIR/challan/arrests from a single yes
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=100
    )

    import json
    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "police_informed": None,
            "fir_registered": None,
            "challan_issued": None,
            "arrests_made": None
        }
def extract_liability_details(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract liability and fault details from a user's message.
Return ONLY a valid JSON object with exactly these keys:

{
  "fault_party": "user / other_party / both / unclear / null",
  "overspeeding": "yes / no / null",
  "signal_violation": "yes / no / null",
  "license_status": "valid / no_license / expired / null",
  "dui": "yes / no / null"
}

Rules:
- fault_party: who appears responsible? user=the person chatting, other_party=the other vehicle
- overspeeding: was excessive speed a factor? yes/no/null if not mentioned
- signal_violation: was a red light or traffic signal violated? yes/no/null if not mentioned
- license_status: valid=had license, no_license=driving without one, expired=expired license, null if not mentioned
- dui: was anyone driving under influence of alcohol or drugs? yes/no/null if not mentioned
- CRITICAL: Only extract what is EXPLICITLY mentioned. Do not infer.
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=100
    )

    import json
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "fault_party": None,
            "overspeeding": None,
            "signal_violation": None,
            "license_status": None,
            "dui": None
        }
def extract_yes_no(user_message, question_context):
    """Extract yes/no for ONE specific pending question — nothing else."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""The user was just asked: "{question_context}"
They replied: "{user_message}"

Classify ONLY their answer to THIS question as exactly one word: YES, NO, or UNCLEAR.
Ignore anything in their message that isn't a direct answer to this specific question.
Reply with ONLY one word, nothing else."""
            }
        ],
        max_tokens=5
    )
    result = response.choices[0].message.content.strip().upper()
    if result == "YES":
        return "yes"
    if result == "NO":
        return "no"
    return None
def extract_evidence_details(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract evidence details from a user's message.
Return ONLY a valid JSON object with exactly these keys:

{
  "evidence": ["list of evidence types mentioned"],
  "has_evidence": "yes / no / null"
}

Evidence types to detect — use these exact strings:
photos, videos, witness_statements, police_report, medical_reports,
insurance_documents, cctv_footage, dashcam_footage

Rules:
- evidence: list ONLY what is explicitly mentioned by the user
- has_evidence:
    yes = user mentioned at least one evidence type OR said they have something
    no = user explicitly said none, nothing, no evidence, don't have anything
    null = completely unclear, user gave no information about evidence
- "I have photos and a police report" → evidence: ["photos", "police_report"], has_evidence: "yes"
- "I don't have anything" → evidence: [], has_evidence: "no"
- "yes" alone → evidence: [], has_evidence: "yes" (they confirmed having something but didn't specify)
- CRITICAL: Only list evidence types that are explicitly named — never infer
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=100
    )

    import json
    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "evidence": [],
            "has_evidence": None
        }
def extract_desired_outcome(user_message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You extract the user's desired legal outcome from their message.
Return ONLY a valid JSON object with exactly this key:

{
  "desired_outcome": "compensation / insurance_claim / criminal_action / fir_registration / court_proceedings / settlement / multiple / unclear"
}

Rules:
- compensation: user wants money for damages, injuries, or losses
- insurance_claim: user wants to file or pursue an insurance claim
- criminal_action: user wants the other party prosecuted, jailed, or punished
- fir_registration: user wants to file an FIR if not already done
- court_proceedings: user wants to take the matter to court
- settlement: user wants an out-of-court resolution or compromise
- multiple: user mentioned more than one of the above outcomes
- unclear: cannot determine from the message at all
- CRITICAL: Only extract what is explicitly stated — never infer
- Return raw JSON only, no explanation, no markdown, no backticks"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=30
    )

    import json
    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"desired_outcome": None}
def extract_legal_analysis(case_facts):
    """
    Takes the full case_state (as a dict) and generates the final legal
    guidance report, matching the exact JSON structure required by the spec.
    """
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
- relevant_pakistani_laws: reference general, well-established Pakistani legal frameworks relevant to
  road accidents (e.g. Motor Vehicles Ordinance 1965, Pakistan Penal Code provisions on negligence/
  rash driving, FIR procedure under CrPC, provincial traffic laws). If unsure of an exact section
  number, describe the law/procedure by name or topic instead of guessing a number.
- rights_and_obligations: describe what each party may be entitled to or responsible for (e.g. right
  to file FIR, right to claim compensation, obligation to cooperate with police), based on the facts.
- recommended_actions: concrete, practical steps (e.g. "file an FIR if not already done", "obtain a
  copy of the medical report", "contact your insurance provider"). Base these on what is still
  missing or pending in the facts (e.g. only mention FIR filing as a next step if one wasn't
  already registered).
- documents_needed: list documents relevant to the user's desired outcome and case facts (e.g. FIR
  copy, medical reports, vehicle registration, insurance policy, CNIC, witness statements).
- NEVER state definitively who was at fault or who will win any claim — describe fault only as
  "based on the facts reported" or similar hedged language.
- ALWAYS include a recommendation to consult a licensed Pakistani lawyer in recommended_actions.
- Keep each list to 3-6 concise, non-redundant items.
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
            "case_summary": "Unable to generate a summary due to a formatting error. Please try again.",
            "incident_type": case_facts.get("incident_type", "road_accident"),
            "relevant_pakistani_laws": [],
            "rights_and_obligations": [],
            "recommended_actions": ["Please consult a licensed Pakistani lawyer for guidance on this case."],
            "documents_needed": [],
            "legal_disclaimer": "This information is educational and not a substitute for professional legal advice."
        }

    # Enforce the exact key set from the spec, regardless of what GPT returned
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