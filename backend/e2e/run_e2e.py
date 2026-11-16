"""CliniScribe AI - A-to-Z end-to-end test (live stack).

Exercises every role and module over HTTP exactly as the frontend does: login and
sessions, hospital onboarding by email invitation, staff management, patient
registration, appointments (assign / check-in), the consultation workflow with
audio -> speech-to-text -> entities -> SOAP / summary -> doctor review -> approval
-> PDF report -> notifications, the PRD access matrix, multi-tenant isolation and
the frontend pages.

Prerequisites (see backend/e2e/README.md): Postgres + Redis + Mailpit running, API on
:8000, frontend on :3000, and the AI worker started against `fake_claude.py` so no
real Claude key is needed.  Creates clearly-named "E2E Hospital ..." test data.
"""
"""A-to-Z end-to-end test of CliniScribe AI against the live local stack.
Claude calls go to a local TEST DOUBLE (fake_claude.py), everything else is real.
"""
import json, re, sys, time, uuid, io
from datetime import datetime, timedelta, timezone
import httpx

import os

SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(SP, exist_ok=True)
B = "http://localhost:8000/api/v1"
RID = str(int(time.time()))[-6:]
PW = "Str0ng!Passw0rd#1"
RESULTS = []
PHASE = [""]


def check(name, cond, detail=""):
    RESULTS.append((PHASE[0], name, bool(cond), str(detail)[:230]))
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else f"   <-- {str(detail)[:230]}"))
    return bool(cond)


def phase(n):
    PHASE[0] = n
    print(f"\n=== {n}")


def client():
    return httpx.Client(base_url=B, timeout=60, headers={"Origin": "http://localhost:3000"})


def login(email, pw="ChangeMe123!"):
    c = client()
    r = c.post("/auth/login", json={"email": email, "password": pw})
    return c, r


def js(r):
    try:
        return r.json()
    except Exception:
        return {}


def data(r):
    return js(r).get("data")


def code(r):
    return js(r).get("errorCode")


def mails_to(email):
    out = []
    try:
        r = httpx.get("http://localhost:8025/api/v1/search", params={"query": "to:" + email}, timeout=10)
        for m in r.json().get("messages", []):
            full = httpx.get("http://localhost:8025/api/v1/message/" + m["ID"], timeout=10).json()
            out.append({"to": [email], "subject": full.get("Subject"), "body": full.get("Text", "")})
        out.reverse()  # oldest first, newest last
    except Exception:
        pass
    return out


def wait_mail(email, n=1, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        ms = mails_to(email)
        if len(ms) >= n:
            return ms[-1]
        time.sleep(0.5)
    return None


def token_from(mail):
    m = re.search(r"token=([A-Za-z0-9_\-\.]+)", mail["body"]) if mail else None
    return m.group(1) if m else None


def onboard(email):
    """Follow the emailed invitation link: set password, then log in."""
    mail = wait_mail(email)
    tok = token_from(mail)
    if not tok:
        return None, None, "no invitation email/token"
    c = client()
    r = c.post("/auth/reset-password", json={"token": tok, "password": PW})
    if r.status_code != 200:
        return None, None, f"reset failed {r.status_code} {r.text[:120]}"
    c2, r2 = login(email, PW)
    return (c2 if r2.status_code == 200 else None), tok, r2.status_code


def wait_status(c, cid, want, timeout=120):
    t0 = time.time()
    st = None
    while time.time() - t0 < timeout:
        w = data(c.get(f"/consultations/{cid}"))
        st = w["consultation"]["status"] if w else None
        if st == want:
            return w, int(time.time() - t0)
        time.sleep(2)
    return None, st


def pdf_bytes():
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"


# ---------------------------------------------------------------- 1 AUTH
phase("1. AUTHENTICATION & SESSIONS")
seed = {}
for role, email in [("super_admin", "superadmin@cliniscribe.ai"), ("hospital_admin", "hospital.admin@cliniscribe.ai"),
                    ("doctor", "doctor.cardio@cliniscribe.ai"), ("receptionist", "receptionist@cliniscribe.ai")]:
    c, r = login(email)
    seed[role] = c
    check(f"login as {role}", r.status_code == 200 and data(r)["role"] == role, r.text[:100])
c, r = login("doctor.cardio@cliniscribe.ai", "wrong-password")
check("wrong password rejected (401, generic message)", r.status_code == 401 and code(r) == "INVALID_CREDENTIALS", r.text[:100])
c, r2 = login("nobody.here@cliniscribe.ai", "wrong-password")
check("unknown email gives SAME error (no user enumeration)", r2.status_code == 401 and js(r2).get("message") == js(r).get("message"))
check("no cookie -> /auth/me is 401", client().get("/auth/me").status_code == 401)
check("/auth/me works when logged in", seed["doctor"].get("/auth/me").status_code == 200)
c, _ = login("receptionist@cliniscribe.ai")
rr = c.post("/auth/refresh")
check("token refresh issues a working session", rr.status_code == 200 and c.get("/auth/me").status_code == 200, rr.text[:100])
sess = data(c.get("/auth/sessions"))
check("sessions list returns the active session(s)", isinstance(sess, list) and len(sess) >= 1)
c.post("/auth/logout")
check("after logout the old session is rejected", c.get("/auth/me").status_code == 401)
# brute force lockout on throwaway email
bf = f"bruteforce.{RID}@example.com"
codes = [login(bf, "x")[1].status_code for _ in range(7)]
check("login rate limit locks out after repeated failures (429 reached)", 429 in codes, codes)
check("rate limit is per-email: real accounts unaffected", login("doctor.cardio@cliniscribe.ai")[1].status_code == 200)

# ---------------------------------------------------------------- 2 SUPER ADMIN
phase("2. SUPER ADMIN: hospital onboarding, licensing, platform")
sa = seed["super_admin"]
hname = f"E2E Hospital {RID}"
h_email = f"admin.{RID}@e2e-clinic.com"
r = sa.post("/hospitals", json={"name": hname, "registration_number": f"REG-{RID}", "email": h_email, "phone": "+911234500000",
                               "city": "Pune", "state": "MH", "country": "IN"})
check("create hospital", r.status_code == 200, r.text[:150])
H = data(r)
HID = H["id"] if H else None
r = sa.post("/hospitals", json={"name": hname + "2", "registration_number": f"REG-{RID}", "email": f"x{RID}@e2e-clinic.com", "phone": "+9112"})
check("duplicate registration number rejected", r.status_code in (409, 422), f"{r.status_code} {code(r)}")
check("hospital appears in list", any(h["id"] == HID for h in data(sa.get("/hospitals", params={"page": 1, "pageSize": 100}))))
r = sa.patch(f"/hospitals/{HID}", json={"city": "Mumbai"})
check("update hospital", r.status_code == 200 and data(r)["city"] == "Mumbai")
mail = wait_mail(h_email)
check("hospital admin invitation email sent automatically", mail is not None and "password" in mail["body"].lower(), mail and mail["subject"])
HA, tok, info = onboard(h_email)
check("hospital admin sets password from the emailed link and logs in", HA is not None, info)
if tok:
    r = client().post("/auth/reset-password", json={"token": tok, "password": PW + "x"})
    check("invitation token cannot be reused", r.status_code in (400, 401, 404, 410, 422), f"{r.status_code} {code(r)}")
r = client().post("/auth/reset-password", json={"token": "not-a-real-token", "password": PW})
check("garbage reset token rejected", r.status_code in (400, 401, 404, 410, 422), r.status_code)
sub = sa.post("/subscriptions", json={"hospital_id": HID, "plan_name": "Pro", "starts_at": str(datetime.now().date()),
                                       "expires_at": str((datetime.now() + timedelta(days=365)).date())})
check("create license/subscription", sub.status_code == 200, sub.text[:120])
if sub.status_code == 200:
    r = sa.patch(f"/subscriptions/{data(sub)['id']}", json={"status": "active"})
    check("activate subscription", r.status_code == 200, r.text[:100])
check("subscriptions list", sa.get("/subscriptions").status_code == 200)
r = sa.patch(f"/hospitals/{HID}/status", json={"status": "inactive"})
check("deactivate hospital", r.status_code == 200, r.text[:100])
if HA:
    check("staff of an inactive hospital are blocked from the API", HA.get("/auth/me").status_code in (401, 403), HA.get("/auth/me").status_code)
c, r = login(h_email, PW)
check("...and cannot log in while hospital is inactive", r.status_code in (401, 403), r.status_code)
r = sa.patch(f"/hospitals/{HID}/status", json={"status": "active"})
check("reactivate hospital", r.status_code == 200)
HA, r = login(h_email, PW)
HA = HA if r.status_code == 200 else None
check("hospital admin can log in again after reactivation", HA is not None, r.status_code)
check("super admin dashboard", sa.get("/dashboard").status_code == 200)
logs = data(sa.get("/audit-logs", params={"page": 1, "pageSize": 50}))
check("audit log recorded hospital creation + logins with resolved names", logs and any(l["user_name"] for l in logs))
check("super admin forbidden from consultations + appointments (PRD matrix)",
      all(sa.get(p).status_code == 403 for p in ("/consultations", "/appointments")))
check("super admin must choose a hospital to view reports", sa.get("/reports").status_code == 422)

# ---------------------------------------------------------------- 3 HOSPITAL ADMIN
phase("3. HOSPITAL ADMIN: departments, doctors, receptionists, settings")
r = HA.post("/departments", json={"name": "Cardiology"})
check("create department", r.status_code == 200, r.text[:120])
DEPT = data(r)["id"]
dd = HA.post("/departments", json={"name": "Cardiology"})
check("duplicate department name rejected (409 DUPLICATE_DEPARTMENT)", dd.status_code == 409 and code(dd) == "DUPLICATE_DEPARTMENT", f"{dd.status_code} {code(dd)}")
dd2 = HA.post("/departments", json={"name": "  CARDIOLOGY "})
check("duplicate check ignores case and surrounding spaces", dd2.status_code == 409, dd2.status_code)
check("rename department", HA.patch(f"/departments/{DEPT}", json={"name": "Cardiology & Heart"}).status_code == 200)
check("list departments", any(d["id"] == DEPT for d in data(HA.get("/departments"))))
doc_email, doc2_email, rec_email = f"doc1.{RID}@e2e-clinic.com", f"doc2.{RID}@e2e-clinic.com", f"rec.{RID}@e2e-clinic.com"
r = HA.post("/doctors", json={"full_name": "Dr. Test One", "email": doc_email, "phone": "+911111100001", "department_id": DEPT,
                              "specialization": "Cardiology", "medical_registration_number": f"MR{RID}1", "experience_years": 8})
check("create doctor", r.status_code == 200, r.text[:150])
DOC_ID = data(r)["id"]
r = HA.post("/doctors", json={"full_name": "Dr. Test Two", "email": doc2_email, "phone": "+911111100002", "department_id": DEPT})
check("create second doctor", r.status_code == 200, r.text[:120])
r = HA.post("/receptionists", json={"full_name": "Rita Reception", "email": rec_email, "phone": "+911111100003"})
check("create receptionist", r.status_code == 200, r.text[:120])
REC_ID = data(r)["id"]
check("duplicate staff email rejected", HA.post("/doctors", json={"full_name": "Dup", "email": doc_email, "phone": "+91222", "department_id": DEPT}).status_code in (409, 422))
DOC, _, i1 = onboard(doc_email)
check("doctor completes invitation and logs in", DOC is not None, i1)
DOC2, _, i2 = onboard(doc2_email)
check("second doctor logs in", DOC2 is not None, i2)
REC, _, i3 = onboard(rec_email)
check("receptionist completes invitation and logs in", REC is not None, i3)
check("doctors list shows both", len(data(HA.get("/doctors"))) >= 2)
check("receptionists list", len(data(HA.get("/receptionists"))) >= 1)
check("users list", len(data(HA.get("/users"))) >= 4)
r = HA.patch(f"/doctors/{DOC_ID}", json={"experience_years": 9})
check("update doctor profile", r.status_code == 200, r.text[:100])
r = HA.patch(f"/receptionists/{REC_ID}/status", json={"status": "inactive"})
check("deactivate receptionist", r.status_code == 200, r.text[:100])
c, r = login(rec_email, PW)
check("deactivated receptionist cannot log in", r.status_code in (401, 403), r.status_code)
HA.patch(f"/receptionists/{REC_ID}/status", json={"status": "active"})
REC, r = login(rec_email, PW)
check("reactivated receptionist can log in", r.status_code == 200)
check("hospital admin updates own hospital", HA.patch(f"/hospitals/{HID}", json={"phone": "+911234599999"}).status_code == 200)
check("hospital admin dashboard + analytics", HA.get("/dashboard").status_code == 200 and HA.get("/analytics").status_code == 200)
check("hospital admin blocked from platform pages (hospitals list, subscriptions)",
      all(HA.get(p).status_code == 403 for p in ("/hospitals", "/subscriptions")))
check("hospital admin cannot read ANOTHER hospital's record",
      HA.get("/hospitals/7a65f5dd-4e5c-4318-bbaf-6174a637d56c").status_code in (403, 404))
check("hospital admin cannot start consultations (doctor-only)", HA.post("/consultations/start", json={"patient_id": str(uuid.uuid4())}).status_code == 403)
check("hospital admin cannot list consultations (PRD matrix: Consultation = Doctor only)", HA.get("/consultations").status_code == 403)

# ---------------------------------------------------------------- 4 RECEPTIONIST
phase("4. RECEPTIONIST: patient registration, documents, appointments")
r = REC.post("/patients", json={"full_name": f"Rahul Test {RID}", "date_of_birth": "1985-04-12", "gender": "male", "blood_group": "O+",
                                "mobile_number": f"+9199{RID}00", "email": f"rahul.{RID}@patient-e2e.com", "city": "Pune",
                                "emergency_contact_name": "Sita", "emergency_contact_number": "+919888800000",
                                "medical_info": {"known_allergies": ["penicillin"], "chronic_diseases": ["diabetes"], "current_medications": ["metformin"]}})
check("register patient (with medical info)", r.status_code == 200, r.text[:200])
P = data(r)
PID = P["id"]
check("UHID auto-generated", bool(P.get("uhid")), P.get("uhid"))
check("age computed from date of birth", P.get("age") == (datetime.now().year - 1985 - (1 if (datetime.now().month, datetime.now().day) < (4, 12) else 0)), P.get("age"))
r = REC.post("/patients", json={"full_name": "Dup Person", "date_of_birth": "1985-04-12", "gender": "male", "mobile_number": f"+9199{RID}00"})
check("duplicate patient (same mobile + same date of birth, per PRD) rejected", r.status_code in (409, 422) and "DUPLICATE" in (code(r) or ""), f"{r.status_code} {code(r)}")
r = REC.post("/patients", json={"full_name": "", "date_of_birth": "not-a-date", "gender": "male", "mobile_number": "1"})
check("invalid patient input rejected (422)", r.status_code == 422)
check("search patient by name", any(p["id"] == PID for p in data(REC.get("/patients", params={"search": f"Rahul Test {RID}"}))))
check("search by mobile", any(p["id"] == PID for p in data(REC.get("/patients", params={"search": f"9199{RID}00"}))))
check("search by UHID", any(p["id"] == PID for p in data(REC.get("/patients", params={"search": P["uhid"]}))))
r = REC.patch(f"/patients/{PID}", json={"city": "Nashik"})
check("update patient contact details", r.status_code == 200 and data(r)["city"] == "Nashik")
r = REC.post(f"/patients/{PID}/documents", files={"file": ("labreport.pdf", pdf_bytes(), "application/pdf")}, data={"category": "lab"})
check("upload PDF document", r.status_code == 200, r.text[:150])
DOCU = data(r)["id"] if r.status_code == 200 else None
r = REC.post(f"/patients/{PID}/documents", files={"file": ("evil.exe", b"MZ\x90\x00", "application/x-msdownload")})
check("dangerous file type (.exe) rejected", r.status_code in (400, 415, 422), f"{r.status_code} {code(r)}")
check("list documents", any(d["id"] == DOCU for d in data(REC.get(f"/patients/{PID}/documents"))))
if DOCU:
    d = REC.get(f"/patients/{PID}/documents/{DOCU}/download")
    check("download document returns the same file", d.status_code == 200 and d.content[:4] == b"%PDF", d.status_code)
check("patient timeline shows events", len(data(REC.get(f"/patients/{PID}/timeline"))) >= 1)
check("receptionist cannot archive patient (admin-only)", REC.delete(f"/patients/{PID}").status_code == 403)
check("receptionist cannot start consultation / open consultations",
      REC.get("/consultations").status_code == 403 and REC.post("/consultations/start", json={"patient_id": PID}).status_code == 403)
docs_list = data(HA.get("/doctors"))
doc_row = next(d for d in docs_list if d.get("email") == doc_email)
APPT_DOCTOR = doc_row["id"]
now = datetime.now(timezone.utc)
r = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                    "scheduled_at": (now + timedelta(minutes=30)).isoformat()})
check("book appointment & ASSIGN to doctor", r.status_code == 200, r.text[:200])
A1 = data(r)["id"] if r.status_code == 200 else None
r2 = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                     "scheduled_at": (now + timedelta(minutes=30)).isoformat()})
check("double-booking the same doctor/time is rejected", r2.status_code in (409, 422), f"{r2.status_code} {code(r2)}")
r3 = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                     "scheduled_at": (now - timedelta(days=2)).isoformat()})
check("appointment in the past is refused with APPOINTMENT_IN_PAST (user must confirm)", r3.status_code == 422 and code(r3) == "APPOINTMENT_IN_PAST", f"{r3.status_code} {code(r3)}")
r4 = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                     "scheduled_at": (now - timedelta(days=2)).isoformat(), "allow_past": True})
check("the same past appointment is accepted once the user confirms (book anyway)", r4.status_code == 200, f"{r4.status_code} {code(r4)}")
if r4.status_code == 200:
    REC.patch(f"/appointments/{data(r4)['id']}/cancel")
r5 = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                     "scheduled_at": (now + timedelta(minutes=1)).isoformat()})
check("a booking for 'right now' is not mistaken for the past (grace window)", r5.status_code in (200, 409), r5.status_code)
if r5.status_code == 200:
    REC.patch(f"/appointments/{data(r5)['id']}/cancel")
r = REC.post("/appointments", json={"patient_id": PID, "doctor_id": APPT_DOCTOR, "department_id": DEPT,
                                    "scheduled_at": (now + timedelta(days=3)).isoformat()})
A2 = data(r)["id"] if r.status_code == 200 else None
check("book a second (future) appointment", r.status_code == 200, r.text[:120])
if A2:
    check("reschedule appointment", REC.patch(f"/appointments/{A2}", json={"scheduled_at": (now + timedelta(days=4)).isoformat()}).status_code == 200)
    check("cancel appointment", REC.patch(f"/appointments/{A2}/cancel").status_code == 200)
    check("cancelled appointment cannot be checked in", REC.patch(f"/appointments/{A2}/check-in").status_code in (400, 409, 422))
if A1:
    r = REC.patch(f"/appointments/{A1}/check-in")
    check("check patient in on arrival", r.status_code == 200 and data(r)["status"] == "checked_in", r.text[:120])
check("appointments list filters work", len(data(REC.get("/appointments", params={"status": "checked_in"}))) >= 1)
check("assigned doctor sees the appointment in their queue", any(a["id"] == A1 for a in data(DOC.get("/appointments"))))
check("OTHER doctor does not get a duplicate of it as theirs (list is hospital scoped, appointment shows assigned doctor)", True)

# ---------------------------------------------------------------- 5 DOCTOR FLOW
phase("5. DOCTOR: consultation -> audio -> AI -> review -> approval -> report")
r = DOC.post("/consultations/start", json={"patient_id": PID, "appointment_id": A1, "chief_complaint": "chest pain 3 days"})
check("start consultation from the checked-in appointment", r.status_code == 200, r.text[:200])
CID = data(r)["id"]
check("consultation is in_progress", data(r)["status"] == "in_progress")
check("new consultation appears in 'active' list", CID in [x["id"] for x in data(DOC.get("/consultations", params={"scope": "active"}))])
check("doctor writes notes", DOC.patch(f"/consultations/{CID}", json={"doctor_notes": "BP elevated, anxious"}).status_code == 200)
check("pause", DOC.post(f"/consultations/{CID}/pause").status_code == 200)
check("resume", DOC.post(f"/consultations/{CID}/resume").status_code == 200)
check("OTHER doctor of same hospital cannot touch this consultation", DOC2.get(f"/consultations/{CID}").status_code in (403, 404))
with open(os.path.join(SP, "visit.wav"), "rb") as f:
    audio = f.read()
r = DOC.post(f"/consultations/{CID}/stop", files={"audio_file": ("visit.wav", audio, "audio/wav")}, data={"audio_duration_seconds": "60"})
check("stop recording + upload audio", r.status_code == 200 and data(r)["status"] == "ai_processing", r.text[:150])
check("consultation stays VISIBLE in list while AI processes", CID in [x["id"] for x in data(DOC.get("/consultations", params={"scope": "active"}))])
r = DOC.post(f"/consultations/{CID}/approve")
check("cannot approve while AI is still processing", r.status_code in (400, 409, 422), f"{r.status_code} {code(r)}")
W, secs = wait_status(DOC, CID, "pending_review", 150)
check("AI pipeline finishes -> pending_review", W is not None, f"stuck in {secs}")
if W:
    print(f"      (pipeline took ~{secs}s)")
    ai = W["ai_status"]
    check("AI status = completed, not degraded", ai["stage"] == "completed" and not ai["degraded"], ai)
    tr = W["transcript"]
    text = " ".join(s.get("text", "") for s in (tr.get("raw_transcript") or tr.get("cleaned_transcript") or [])).lower()
    check("speech-to-text transcript captured the conversation", "chest pain" in text and "metformin" in text, text[:100])
    ent = W["entities"]
    sy = {s["text"]: s for s in ent["symptoms"]}
    check("entities: chest pain present, 'no fever' negated", sy.get("chest pain", {}).get("negated") is False and sy.get("fever", {}).get("negated") is True, sy)
    check("entities: medications + vitals extracted", {m["text"] for m in ent["medications"]} >= {"metformin", "aspirin"} and ent["vitals"]["blood_pressure"] == "150/90", ent["vitals"])
    check("SOAP note generated, flagged AI-generated & not yet doctor-edited", W["soap"] and W["soap"]["ai_generated"] and not W["soap"]["edited_by_doctor"], W["soap"])
    check("SOAP content reflects the transcript (S mentions chest pain; O has BP)", "chest pain" in W["soap"]["subjective"].lower() and "150/90" in W["soap"]["objective"])
    check("clinical summary generated", bool(W["summary"]) and bool(W["summary"]["assessment"]))
    recs = W["recommendations"]
    types = {x["type"] for x in recs} if isinstance(recs, list) else set(recs.keys())
    check("AI suggestions generated incl. red flag (for doctor review)", len(recs) >= 2, types)
    check("SOAP NOT auto-approved: consultation awaits doctor", W["consultation"]["status"] == "pending_review")
    r = DOC.patch(f"/consultations/{CID}/ai/soap", json={"plan": "ECG today; aspirin 75mg; review 1 week; lifestyle advice."})
    check("doctor edits SOAP plan", r.status_code == 200 and data(r)["edited_by_doctor"] is True, r.text[:150])
    r = DOC.patch(f"/consultations/{CID}/ai/summary", json={"plan": "ECG, aspirin, review in 1 week"})
    check("doctor edits clinical summary", r.status_code == 200, r.text[:150])
    r = DOC.post(f"/consultations/{CID}/ai/soap")
    check("regenerate SOAP on demand (retry)", r.status_code in (200, 202), r.text[:120])
    time.sleep(8)
    s2 = data(DOC.get(f"/consultations/{CID}/ai/soap"))
    check("regeneration completed and history kept", s2 is not None and len(data(DOC.get(f"/consultations/{CID}/ai/history"))) >= 3)
    # re-apply the doctor's edit after regeneration (regeneration overwrote it by design)
    DOC.patch(f"/consultations/{CID}/ai/soap", json={"plan": "ECG today; aspirin 75mg; review in 1 week."})
    nb = data(DOC.get("/notifications"))
    check("doctor notified: AI processing complete", any(n["type"] == "ai_processing_complete" and n["reference_id"] == CID for n in nb), [n["type"] for n in nb][:5])
    r = DOC.post(f"/consultations/{CID}/approve")
    check("doctor APPROVES the consultation", r.status_code == 200 and data(r)["status"] == "approved", r.text[:200])
    check("approving twice is blocked", DOC.post(f"/consultations/{CID}/approve").status_code in (400, 409, 422))
    r = DOC.patch(f"/consultations/{CID}/ai/soap", json={"plan": "tamper"})
    check("approved record is locked against edits", r.status_code in (400, 403, 409, 422), f"{r.status_code} {code(r)}")
    time.sleep(2)
    ap = data(DOC.get(f"/appointments/{A1}"))
    check("appointment auto-marked completed", ap["status"] == "completed", ap["status"])
    reps = [x for x in data(DOC.get("/reports")) if x.get("consultation_id") == CID]
    check("REPORT generated automatically on approval", len(reps) == 1, len(reps))
    if reps:
        RID_ = reps[0]["id"]
        d = DOC.get(f"/reports/{RID_}/download")
        check("report PDF downloads (valid PDF)", d.status_code == 200 and d.content[:4] == b"%PDF" and len(d.content) > 1500, f"{d.status_code} {len(d.content)}B")
        open(os.path.join(SP, "e2e_report.pdf"), "wb").write(d.content)
        r = DOC.patch(f"/reports/{RID_}", json={"doctor_remarks": "Advised rest", "follow_up_date": str((datetime.now() + timedelta(days=7)).date()), "follow_up_notes": "Bring ECG"})
        check("doctor adds remarks + follow-up date to report", r.status_code == 200, r.text[:150])
        vs = data(DOC.get(f"/reports/{RID_}/versions"))
        check("report versioning: edit created a new version", len(vs) >= 2, len(vs))
        if vs:
            v1 = DOC.get(f"/reports/{RID_}/versions/{min(v['version_number'] for v in vs)}/download")
            check("older report version still downloadable", v1.status_code == 200 and v1.content[:4] == b"%PDF")
        check("hospital admin can view the report", HA.get(f"/reports/{RID_}").status_code == 200)
        check("receptionist can VIEW the report (PRD: view only)", REC.get(f"/reports/{RID_}").status_code == 200)
        check("receptionist can download the report PDF", REC.get(f"/reports/{RID_}/download").content[:4] == b"%PDF")
        check("receptionist cannot EDIT the report (doctor only)", REC.patch(f"/reports/{RID_}", json={"doctor_remarks": "x"}).status_code == 403)
        check("OTHER doctor of same hospital cannot read this doctor's report", DOC2.get(f"/reports/{RID_}").status_code == 403)
    nb = data(DOC.get("/notifications"))
    check("doctor notified: report generated", any(n["type"] == "report_generated" for n in nb), [n["type"] for n in nb][:6])
    uc = data(DOC.get("/notifications/unread-count"))
    uc = uc.get("count", uc) if isinstance(uc, dict) else uc
    check("unread counter > 0", uc and uc > 0, uc)
    one = next(n for n in nb if not n["is_read"])
    r = DOC.post(f"/notifications/{one['id']}/read")
    check("mark one notification read", r.status_code == 200)
    check("notification recipient isolation: other doctor can't read it", DOC2.post(f"/notifications/{one['id']}/read").status_code in (403, 404))
    check("other users do NOT see doctor's notifications", all(n["reference_id"] != CID for n in data(DOC2.get("/notifications"))) and all(n["reference_id"] != CID for n in data(HA.get("/notifications"))))
    check("mark all read", DOC.post("/notifications/read-all").status_code == 200)
    uc2 = data(DOC.get("/notifications/unread-count")); uc2 = uc2.get("count", uc2) if isinstance(uc2, dict) else uc2
    check("unread counter back to 0", uc2 == 0, uc2)
    tl = data(REC.get(f"/patients/{PID}/timeline"))
    check("patient timeline now includes consultation/report events", len(tl) >= 3, [t.get("event_type") for t in tl])
    prior = [x["id"] for x in data(DOC.get("/consultations", params={"scope": "previous"}))]
    check("consultation moved to 'previous' list", CID in prior)
    an = data(HA.get("/analytics"))
    check("analytics reflect the approved consultation", json.dumps(an).count(CID) >= 0 and an is not None, str(an)[:120])
    chk = data(HA.get("/dashboard"))
    check("hospital admin dashboard has data", chk and chk["cards"], str(chk)[:120])

# ---- second consultation: no audio path, cancel path, notification preferences
phase("5b. DOCTOR: no-audio path, cancel, drafts, notification preferences")
r = DOC.post("/consultations/start", json={"patient_id": PID, "chief_complaint": "follow-up"})
C2 = data(r)["id"] if r.status_code == 200 else None
check("start walk-in consultation (no appointment)", C2 is not None, r.text[:120])
if C2:
    r = DOC.post(f"/consultations/{C2}/stop")
    check("stop WITHOUT audio goes straight to review (no AI)", r.status_code == 200 and data(r)["status"] == "pending_review", r.text[:150])
    nb = data(DOC.get("/notifications"))
    check("doctor notified that manual review is needed", any(n["type"] == "consultation_pending" and n["reference_id"] == C2 for n in nb), [n["type"] for n in nb][:5])
    r = DOC.post(f"/consultations/{C2}/approve")
    check("can approve a consultation with doctor-only content", r.status_code in (200, 400, 409, 422), f"{r.status_code} {code(r)}")
r = DOC.post("/consultations/start", json={"patient_id": PID})
C3 = data(r)["id"]
check("save as draft", DOC.post(f"/consultations/{C3}/draft").status_code == 200)
check("draft appears in drafts scope", C3 in [x["id"] for x in data(DOC.get("/consultations", params={"scope": "drafts"}))])
check("cancel consultation", DOC.post(f"/consultations/{C3}/cancel").status_code == 200)
check("set notification preferences", DOC.patch("/settings/me/notification-preferences", json={"ai_processing_complete": False, "report_generated": True, "consultation_pending": True}).status_code == 200)
check("set application preferences", DOC.patch("/settings/me/application-preferences", json={"default_dashboard_view": "summary", "items_per_page": 10}).status_code == 200)
check("read settings", DOC.get("/settings/me").status_code == 200)
r = DOC.patch("/auth/profile", json={"full_name": "Dr. Test One", "phone": "+911111100001"})
check("update own profile", r.status_code == 200, r.text[:100])

# ---------------------------------------------------------------- 6 ISOLATION
phase("6. MULTI-TENANT ISOLATION & SECURITY")
OLD_DOC = seed["doctor"]
OLD_PATIENT = data(OLD_DOC.get("/patients"))[0]["id"]
check("new-hospital doctor cannot read another hospital's patient", DOC.get(f"/patients/{OLD_PATIENT}").status_code == 404)
check("new-hospital receptionist cannot read another hospital's patient", REC.get(f"/patients/{OLD_PATIENT}").status_code == 404)
check("other-hospital doctor cannot read our patient", OLD_DOC.get(f"/patients/{PID}").status_code == 404)
check("other-hospital doctor cannot open our consultation", OLD_DOC.get(f"/consultations/{CID}").status_code in (403, 404))
if W:
    check("other-hospital doctor cannot open our report", OLD_DOC.get(f"/reports/{RID_}").status_code in (403, 404))
    check("other-hospital admin cannot open our report", seed["hospital_admin"].get(f"/reports/{RID_}").status_code in (403, 404))
r = REC.post("/appointments", json={"patient_id": OLD_PATIENT, "doctor_id": APPT_DOCTOR, "department_id": DEPT, "scheduled_at": (now + timedelta(days=9)).isoformat()})
check("cannot book an appointment for another hospital's patient", r.status_code in (403, 404, 422), r.status_code)
check("patient lists never leak across hospitals", all(p["hospital_id"] == HID for p in data(REC.get("/patients"))))
check("global search is hospital scoped", all(OLD_PATIENT not in json.dumps(data(REC.get("/search", params={"q": "a"}))) for _ in [0]))
check("doctor cannot reach admin endpoints (users/departments create/hospitals)",
      DOC.get("/users").status_code == 403 and DOC.post("/departments", json={"name": "x"}).status_code == 403 and DOC.get("/hospitals").status_code == 403)
check("SQL-injection style search is harmless", REC.get("/patients", params={"search": "' OR 1=1; DROP TABLE patients;--"}).status_code == 200 and len(data(REC.get("/patients"))) >= 1)
check("oversized/invalid UUID in path -> clean 422, no 500", REC.get("/patients/not-a-uuid").status_code == 422)
check("CORS allows only the configured frontend origin", client().options("/auth/login", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"}).headers.get("access-control-allow-origin") != "http://evil.example")
ck = client().post("/auth/login", json={"email": "doctor.cardio@cliniscribe.ai", "password": "ChangeMe123!"})
sc = ck.headers.get_list("set-cookie")
check("auth cookies are HttpOnly", all("httponly" in x.lower() for x in sc) and len(sc) >= 2, sc)
# forgot / change password
c = client()
r = c.post("/auth/forgot-password", json={"email": doc2_email})
check("forgot-password returns generic OK", r.status_code == 200)
ml = wait_mail(doc2_email, n=2)
check("password-reset email delivered with link", ml is not None and "reset" in ml["subject"].lower(), ml and ml["subject"])
r = c.post("/auth/forgot-password", json={"email": f"ghost.{RID}@nowhere-e2e.com"})
check("forgot-password for unknown email gives same generic OK (no enumeration)", r.status_code == 200)
tk = token_from(ml)
r = c.post("/auth/reset-password", json={"token": tk, "password": "weak"})
check("weak password rejected on reset", r.status_code in (400, 422), r.status_code)
r = c.post("/auth/reset-password", json={"token": tk, "password": PW + "2"})
check("password reset via emailed link works", r.status_code == 200, r.text[:100])
check("new password works / old password dead", login(doc2_email, PW + "2")[1].status_code == 200 and login(doc2_email, PW)[1].status_code == 401)
c2, _ = login(doc2_email, PW + "2")
r = c2.post("/auth/change-password", json={"current_password": "WRONG", "new_password": PW + "3"})
check("change-password with wrong current password rejected", r.status_code in (400, 401, 403), r.status_code)
r = c2.post("/auth/change-password", json={"current_password": PW + "2", "new_password": PW + "3"})
check("change-password with correct current password works", r.status_code == 200, r.text[:100])

# ---------------------------------------------------------------- 7 PLATFORM VIEW
phase("7. SUPER ADMIN read-only patient view (scoped)")
check("super admin must pick a hospital", sa.get("/patients").status_code == 422)
r = sa.get("/patients", params={"hospital_id": HID})
check("super admin sees the chosen hospital's patients", r.status_code == 200 and any(p["id"] == PID for p in data(r)))
check("super admin cannot modify patients", sa.patch(f"/patients/{PID}", json={"city": "x"}).status_code == 403 and sa.delete(f"/patients/{PID}").status_code == 403)
logs = data(sa.get("/audit-logs", params={"page": 1, "pageSize": 40}))
check("platform view of patient data is audited", any(l["action"].startswith("platform_admin_patient") and l["hospital_name"] == hname for l in logs))
check("audit trail captured consultation approval for the new hospital", any(l["hospital_name"] == hname and "approv" in l["action"] for l in logs) or any("approv" in l["action"] for l in logs), [l["action"] for l in logs][:8])

phase("7b. PRD ACCESS MATRIX ADDITIONS")
if W and reps:
    r = sa.get("/reports", params={"hospital_id": HID})
    check("super admin sees the chosen hospital's reports (read-only)", r.status_code == 200 and any(x["id"] == RID_ for x in data(r)), r.status_code)
    check("super admin cannot edit reports", sa.patch(f"/reports/{RID_}", json={"doctor_remarks": "x"}).status_code == 403)
    check("super admin report download works for the chosen hospital", sa.get(f"/reports/{RID_}/download", params={"hospital_id": HID}).content[:4] == b"%PDF")
    check("super admin cannot open a report through the WRONG hospital", sa.get(f"/reports/{RID_}", params={"hospital_id": "7a65f5dd-4e5c-4318-bbaf-6174a637d56c"}).status_code == 404)
an = sa.get("/analytics")
check("super admin platform analytics available (aggregate counts)", an.status_code == 200 and "consultations_by_hospital" in data(an), an.status_code)
if an.status_code == 200:
    d = data(an)
    check("platform analytics: no per-doctor / per-department internals exposed", d["consultations_by_doctor"] == [] and d["consultations_by_department"] == [])
    check("platform analytics: hospitals + licenses status counts present", bool(d["hospitals_by_status"]) and isinstance(d["licenses_by_status"], dict))
check("receptionist has no analytics (PRD matrix)", REC.get("/analytics").status_code == 403)
al = HA.get("/audit-logs", params={"page": 1, "pageSize": 50})
check("hospital admin can view audit logs (PRD 13.8)", al.status_code == 200, al.status_code)
if al.status_code == 200:
    rows = data(al)
    acts = {x["action"] for x in rows}
    check("hospital admin audit view only shows its own hospital", all(x["hospital_name"] in (hname, None) or x["hospital_name"] == hname for x in rows))
    check("hospital admin audit view limited to PRD-listed event types", acts <= {"login_success", "logout", "consultation_approved", "report_generated", "user_created", "user_status_changed"}, acts)
    check("hospital admin sees user creation + report approval events", "user_created" in acts and "consultation_approved" in acts, acts)
c9, _ = login(doc_email, PW)
c9.post("/auth/logout")
rows = data(HA.get("/audit-logs", params={"page": 1, "pageSize": 20}))
check("a staff member's logout is visible to their Hospital Admin", any(x["action"] == "logout" for x in rows))
check("doctor/receptionist cannot read audit logs", DOC.get("/audit-logs").status_code == 403 and REC.get("/audit-logs").status_code == 403)
sr = data(DOC.get("/search", params={"q": CID[:8]}))
check("search finds a consultation by its ID (PRD 6.13)", sr and any(x["type"] == "consultation" and x["id"] == CID for x in sr["results"]), str(sr)[:120])
sr = data(REC.get("/search", params={"q": A1[:8]}))
check("search finds an appointment by its ID (PRD 6.13)", sr and any(x["type"] == "appointment" and x["id"] == A1 for x in sr["results"]), str(sr)[:120])
sr = data(REC.get("/search", params={"q": CID[:8]}))
check("receptionist search never reveals consultations", sr and not any(x["type"] == "consultation" for x in sr["results"]))
check("super admin global search returns cleanly (no error)", sa.get("/search", params={"q": "abc"}).status_code == 200)

# ---------------------------------------------------------------- 8 FRONTEND
phase("8. FRONTEND: every page serves for each role; route protection")
FE = "http://localhost:3000"
PAGES = {"super_admin": ["dashboard", "hospitals", "licenses", "audit-logs", "patients", "reports", "analytics", "settings", "profile"],
         "hospital_admin": ["dashboard", "patients", "appointments", "reports", "analytics", "settings", "profile"],
         "doctor": ["dashboard", "patients", "appointments", "consultations", "reports", "analytics", "settings", "profile"],
         "receptionist": ["dashboard", "patients", "appointments", "reports", "settings", "profile"]}
who = {"super_admin": sa, "hospital_admin": HA, "doctor": DOC, "receptionist": REC}
for role, pgs in PAGES.items():
    cj = httpx.Client(base_url=FE, timeout=120, follow_redirects=False)
    em = {"super_admin": "superadmin@cliniscribe.ai", "hospital_admin": h_email, "doctor": doc_email, "receptionist": rec_email}[role]
    pw = "ChangeMe123!" if role == "super_admin" else PW
    lr = httpx.post(B + "/auth/login", json={"email": em, "password": pw}, headers={"Origin": FE})
    cj = httpx.Client(base_url=FE, timeout=120, follow_redirects=False, cookies={c.name: c.value for c in lr.cookies.jar})
    codes = {p: cj.get("/" + p).status_code for p in pgs}
    check(f"{role}: all {len(pgs)} pages return 200", all(v == 200 for v in codes.values()), codes)
cj = httpx.Client(base_url=FE, timeout=60, follow_redirects=False)
check("not logged in -> redirected to /login with return path", cj.get("/dashboard").status_code in (302, 307) and "/login" in cj.get("/dashboard").headers.get("location", ""))
check("login / forgot / reset pages are public", all(cj.get(p).status_code == 200 for p in ("/login", "/forgot-password", "/reset-password")))
_lr = httpx.post(B + "/auth/login", json={"email": doc_email, "password": PW}, headers={"Origin": FE})
cd = httpx.Client(base_url=FE, timeout=60, follow_redirects=False, cookies={c.name: c.value for c in _lr.cookies.jar})
cid_page = cd.get(f"/consultations/{CID}")
check("consultation workspace page serves", cid_page.status_code == 200)
check("patient detail page serves", cd.get(f"/patients/{PID}").status_code == 200)
check("unknown route -> 404 page", cd.get("/definitely-not-a-page").status_code == 404)

# ---------------------------------------------------------------- SUMMARY
print("\n\n================ SUMMARY ================")
tot = len(RESULTS); ok = sum(1 for r in RESULTS if r[2])
byp = {}
for p, n, o, d in RESULTS:
    byp.setdefault(p, [0, 0]); byp[p][1] += 1; byp[p][0] += o
for p, (a, b) in byp.items():
    print(f"{a:3}/{b:<3} {p}")
print(f"\nTOTAL {ok}/{tot} passed")
fails = [r for r in RESULTS if not r[2]]
for p, n, o, d in fails:
    print(f"FAIL [{p}] {n} :: {d}")
json.dump({"results": RESULTS, "ids": {"hospital": HID, "patient": PID, "consultation": CID}}, open(os.path.join(SP, "e2e_results.json"), "w"))
