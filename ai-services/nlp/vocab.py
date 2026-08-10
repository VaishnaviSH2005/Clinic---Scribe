"""Curated medical vocabulary used by the keyword/phrase-matching entity
extractor (see `entity_extractor.py` for why this substitutes for
SciSpaCy/MedCAT in this milestone). Lists are intentionally small and
common-consultation-focused rather than exhaustive — this is the documented
swap-in point for a licensed MedCAT model pack.
"""

SYMPTOMS = [
    "fever", "cough", "headache", "sore throat", "runny nose", "nasal congestion",
    "chest pain", "shortness of breath", "difficulty breathing", "breathlessness",
    "abdominal pain", "stomach pain", "nausea", "vomiting", "diarrhea", "constipation",
    "dizziness", "fatigue", "weakness", "body ache", "joint pain", "back pain",
    "chills", "sweating", "loss of appetite", "weight loss", "weight gain",
    "palpitations", "swelling", "rash", "itching", "blurred vision", "ear pain",
    "loss of consciousness", "heavy bleeding", "low oxygen saturation", "wheezing",
    "insomnia", "anxiety", "numbness", "tingling", "cramps", "bloating",
]

MEDICATIONS = [
    "paracetamol", "acetaminophen", "ibuprofen", "aspirin", "amoxicillin",
    "azithromycin", "metformin", "insulin", "atorvastatin", "amlodipine",
    "losartan", "omeprazole", "pantoprazole", "cetirizine", "montelukast",
    "salbutamol", "albuterol", "levothyroxine", "metoprolol", "furosemide",
    "prednisone", "dexamethasone", "warfarin", "clopidogrel", "vitamin d",
    "vitamin b12", "calcium", "iron supplement", "antibiotic", "antihistamine",
]

ALLERGIES = [
    "penicillin", "sulfa", "peanut", "shellfish", "latex", "dust", "pollen",
    "aspirin allergy", "nsaid allergy", "egg allergy", "milk allergy", "lactose",
]

CHRONIC_CONDITIONS = [
    "diabetes", "hypertension", "asthma", "copd", "arthritis", "thyroid disorder",
    "hypothyroidism", "hyperthyroidism", "coronary artery disease", "heart disease",
    "chronic kidney disease", "epilepsy", "depression", "anxiety disorder",
    "obesity", "hyperlipidemia", "high cholesterol", "migraine",
]

NEGATION_TRIGGERS = ["no ", "not ", "denies ", "denied ", "without ", "negative for ", "no history of "]

SEVERITY_QUALIFIERS = {
    "severe": ["severe", "extreme", "intense", "excruciating", "worst"],
    "moderate": ["moderate", "noticeable", "persistent"],
    "mild": ["mild", "slight", "minor", "occasional"],
}
