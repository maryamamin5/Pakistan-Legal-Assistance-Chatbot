# Pakistan Road Accident Legal Assistance Chatbot

An AI-powered conversational chatbot that guides users through a structured legal
intake process for road accident cases in Pakistan. Built with OpenAI's GPT-4o-mini,
it collects case facts step by step, then generates an educational legal guidance
report aligned with general Pakistani law.

This chatbot does **not** replace a lawyer. It provides educational and
informational guidance only, and always recommends consulting a licensed
Pakistani lawyer for actual legal advice.

---

## How It Works

The bot conducts a 9-step structured interview, storing every confirmed answer
in a persistent in-memory case state. Each step asks one focused question at a
time, waits for a clear answer, and only advances once that specific field is
confidently filled — no skipping ahead, no guessing.

### Conversation Flow

1. **Incident Identification** — determines the type of legal issue (road
   accident, property dispute, employment issue, etc.). Only road accident
   cases are supported at this stage; other case types are politely redirected.
2. **Basic Incident Details** — date, city/province, road type, number of
   vehicles involved.
3. **Injury Assessment** — whether anyone was injured, severity (minor,
   serious, fatal), and whether medical treatment was required.
4. **Property Damage Assessment** — vehicle damage level, public/private
   property damage, and estimated financial loss.
5. **Police Involvement** — whether police were informed, FIR registration,
   traffic challan, and arrests. If police were never informed, the remaining
   sub-questions are automatically skipped.
6. **Liability Assessment** — who appears responsible, overspeeding, signal
   violation, license status, and driving under influence. The bot only
   collects facts here and never states a legal conclusion about fault.
7. **Evidence Collection** — photos/videos, witness statements, police report,
   medical reports, insurance documents.
8. **Desired Outcome** — what the user wants to achieve (compensation,
   insurance claim, criminal action, FIR registration, court proceedings,
   settlement). Multiple outcomes can be selected at once.
9. **Legal Analysis & Guidance** — once all facts are collected, the bot
   generates a structured legal guidance report: a case summary, relevant
   Pakistani laws, rights and obligations, recommended next steps, and
   required documentation. The full session is also saved to a local JSON file.

---

## Guardrails

The chatbot enforces topic boundaries throughout the conversation:

**Allowed**
- Questions strictly relevant to the reported legal issue
- Following the predefined step-by-step flow
- Explaining Pakistani laws in plain language
- Educational legal guidance

**Restricted / redirected**
- Political discussions
- Religious debates
- Medical diagnosis
- Financial investment advice
- Anything unrelated to the reported legal issue
- Requests for illegal activity
- Questions outside the scope of Pakistani law

If a message goes off-topic, the bot responds with a redirect (e.g. *"I can
only assist with your legal matter. Let's continue — [current question]"*)
and repeats the question it's currently waiting on.

---

## Setup

1. Clone the repository and create a virtual environment:
python -m venv .venv
.venv\Scripts\activate      # Windows

2. Install dependencies:
pip install openai

3. Add your OpenAI API key. Create a `.env` file or set it as an environment
   variable, then load it in `utils/openai_client.py`:
```python
   from openai import OpenAI
   client = OpenAI(api_key="your-api-key-here")
```

4. Run the chatbot:
python main.py

---

## Design Principles

A few hard-learned rules shaped this codebase, and are worth following if
you extend it:

- **GPT never decides what question to ask next.** Every question the bot
  asks is a hardcoded string. GPT is only used for two things: extracting
  structured data from free-text answers, and generating the final legal
  report in Step 9. Letting GPT choose the next question reliably causes it
  to drift off-script.
- **Every extractor call needs question context.** A bare "yes" or "no" means
  nothing to a model without knowing what was just asked. Functions like
  `extract_yes_no(user_message, question_context)` always pass in the pending
  question explicitly.
- **Lock fields once they're confirmed.** Every write to `case_state` is
  guarded with `if not case_state[field]`, so a later ambiguous message can
  never silently overwrite an already-confirmed answer.
- **Fields that can have multiple values (evidence, desired outcome) are
  lists, not single values.** Users often want more than one outcome or have
  more than one type of evidence — the state and extractors reflect that.

---

## Output Format

Step 9 produces a JSON report saved to `sessions/session_<timestamp>.json`,
containing the full collected case facts alongside a generated legal
analysis in this structure:

```json
{
  "case_summary": "...",
  "incident_type": "road_accident",
  "relevant_pakistani_laws": ["...", "..."],
  "rights_and_obligations": ["...", "..."],
  "recommended_actions": ["...", "..."],
  "documents_needed": ["...", "..."],
  "legal_disclaimer": "This information is educational and not a substitute for professional legal advice."
}
```

---

## Disclaimer

This tool is for educational purposes only and does not constitute legal
advice. Always consult a licensed l
