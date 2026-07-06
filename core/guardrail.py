from utils.openai_client import client

def is_on_topic(user_message, current_step=1):
    
    # Short answers (4 words or fewer) always pass mid-conversation
    # "yes", "no", "minor", "serious", "total loss", "2 cars" etc.
    if current_step > 1 and len(user_message.strip().split()) <= 4:
        return True
    if current_step > 1:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a classifier for a Pakistan legal chatbot.
The user is answering structured intake questions about their legal case.
Your job: only block messages that are COMPLETELY unrelated to the legal case.

Always return LEGAL for:
- Dates, locations, road types, vehicle counts
- Yes/no answers to any question
- Injury descriptions, hospital visits, medical treatment mentioned in context of an accident
- Police, FIR, damage, evidence, compensation related answers
- Anything that could reasonably be an answer to a legal intake question

Only return OFFTOPIC for clear irrelevant messages like:
- Weather, food, sports, politics, religion
- Random gibberish with no connection to their case
- Asking about something completely unrelated

Reply with ONLY one word: LEGAL or OFFTOPIC. No explanation."""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=5
        )
        result = response.choices[0].message.content.strip().upper()
        return result == "LEGAL"

    # Step 1 only — strict check
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a strict classifier for a Pakistan legal chatbot.
Decide if the user's message is related to a legal matter in Pakistan.

Legal topics: accidents, FIR, police, courts, property disputes, employment issues,
consumer complaints, cybercrimes, theft, robbery, insurance, compensation, lawyers.

Off-topic: weather, sports, cooking, politics, religion, medical diagnosis,
financial investment, random small talk.

Reply with ONLY one word: LEGAL or OFFTOPIC. No explanation. No punctuation."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=5
    )
    result = response.choices[0].message.content.strip().upper()
    return result == "LEGAL"