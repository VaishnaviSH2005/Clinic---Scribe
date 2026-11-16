"""TEST DOUBLE for the Anthropic Messages API (NOT real Claude).

Returns schema-valid JSON for each CliniScribe prompt, built only from the
entities/transcript the pipeline sends — so it verifies the integration
(request format -> parse -> persist -> UI/report), not clinical quality.
"""
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

CALLS = []


def build(system: str, user: str) -> dict:
    m = re.search(r"Context:\n(.*)\n\nReturn only", user, re.S)
    ctx = json.loads(m.group(1)) if m else {}
    ent = ctx.get("extracted_entities") or {}
    present = [s["text"] for s in ent.get("symptoms", []) if not s.get("negated")]
    absent = [s["text"] for s in ent.get("symptoms", []) if s.get("negated")]
    meds = [x["text"] for x in ent.get("medications", [])]
    vit = ent.get("vitals") or {}
    bp = vit.get("blood_pressure", "not recorded")
    subj = "Patient reports " + (", ".join(present) or "no symptoms") + "."
    if absent:
        subj += " Denies " + ", ".join(absent) + "."
    obj = f"Blood pressure {bp}. Current medications: {', '.join(meds) or 'none'}."
    s = system.lower()
    if "concise consultation" in s:
        return {
            "chief_complaint": ", ".join(present) or "n/a",
            "history_of_present_illness": subj,
            "key_findings": obj,
            "assessment": "Findings warrant cardiac evaluation.",
            "plan": "ECG, start aspirin, review in one week.",
            "confidence": "medium",
        }
    if "possible diagnoses" in s and "clinical decision support" in s:
        return {
            "possible_diagnoses": [
                {"content": "Stable angina", "explanation": "Exertional chest pain with dyspnoea.", "confidence": "medium"}
            ],
            "recommended_tests": [
                {"content": "12-lead ECG", "explanation": "Chest pain on exertion.", "confidence": "high"}
            ],
        }
    if "red flag" in s or "clinical safety assistant" in s:
        flags = []
        if "chest pain" in present:
            flags.append({"content": "Chest pain with shortness of breath", "explanation": "Stated by patient.", "confidence": "high"})
        return {"red_flags": flags}
    return {
        "subjective": subj,
        "objective": obj,
        "assessment": "Chest pain on exertion, possible cardiac origin (for doctor review).",
        "plan": "ECG; aspirin as discussed; follow up in 1 week.",
        "confidence": "medium",
    }


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        system = body.get("system", "")
        if isinstance(system, list):
            system = " ".join(b.get("text", "") for b in system)
        user = body["messages"][0]["content"]
        if isinstance(user, list):
            user = " ".join(b.get("text", "") for b in user)
        out = build(system, user)
        CALLS.append(list(out.keys())[0])
        resp = {
            "id": "msg_fake",
            "type": "message",
            "role": "assistant",
            "model": body.get("model", "fake"),
            "content": [{"type": "text", "text": json.dumps(out)}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
        data = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        data = json.dumps({"calls": CALLS}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


HTTPServer(("127.0.0.1", 8765), H).serve_forever()
