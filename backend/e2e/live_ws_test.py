"""Live captions over a real WebSocket (server side). Needs the API, Redis and the live worker running."""
"""Live captions: end-to-end over a real WebSocket (server side)."""
import asyncio
import json
import time
import wave

import httpx
import numpy as np
import websockets

import os

SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
B = "http://localhost:8000/api/v1"
WS = "ws://localhost:8000/api/v1"
ORIGIN = "http://localhost:3000"
R = []


def check(name, cond, detail=""):
    R.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else f"   <-- {detail}"))


def login(email, pw="ChangeMe123!"):
    c = httpx.Client(base_url=B, timeout=30, headers={"Origin": ORIGIN})
    r = c.post("/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    cookie = "; ".join(f"{k}={v}" for k, v in c.cookies.items())
    return c, cookie


def pcm16k(path):
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if sr != 16000:
        t_new = np.linspace(0, len(data) - 1, int(len(data) * 16000 / sr))
        data = np.interp(t_new, np.arange(len(data)), data)
    return data.astype("<i2").tobytes(), sr


async def expect_close(label, cookie, cid, origin=ORIGIN, expect=None):
    try:
        headers = {"Origin": origin} if origin else {}
        if cookie:
            headers["Cookie"] = cookie
        async with websockets.connect(f"{WS}/consultations/{cid}/live", additional_headers=headers, open_timeout=10) as ws:
            try:
                await asyncio.wait_for(ws.recv(), 3)
                check(label, False, "connection stayed open")
            except websockets.ConnectionClosed as e:
                check(label, e.rcvd is not None and e.rcvd.code == expect, f"closed with {e.rcvd.code if e.rcvd else None}")
            except asyncio.TimeoutError:
                check(label, False, "connection accepted (no close)")
    except websockets.InvalidStatus as e:
        check(label, expect is not None, f"HTTP {e.response.status_code}")
    except websockets.ConnectionClosed as e:
        check(label, e.rcvd is not None and e.rcvd.code == expect, f"closed with {e.rcvd.code if e.rcvd else None}")


async def main():
    doc, doc_cookie = login("doctor.cardio@cliniscribe.ai")
    rec, rec_cookie = login("receptionist@cliniscribe.ai")
    other, other_cookie = login("doctor.ortho@cliniscribe.ai")
    pid = doc.get("/patients").json()["data"][0]["id"]
    cid = doc.post("/consultations/start", json={"patient_id": pid, "chief_complaint": "LIVE-CAPTION TEST"}).json()["data"]["id"]
    print("consultation", cid)

    print("\n--- security")
    await expect_close("no login cookie -> refused (4401)", "", cid, expect=4401)
    await expect_close("receptionist -> refused (4403)", rec_cookie, cid, expect=4403)
    await expect_close("other doctor -> refused (4404)", other_cookie, cid, expect=4404)
    await expect_close("foreign website Origin -> refused (4403)", doc_cookie, cid, origin="http://evil.example", expect=4403)
    await expect_close("unknown consultation -> refused (4404)", doc_cookie, "00000000-0000-0000-0000-000000000000", expect=4404)

    print("\n--- live captions (real-time pace)")
    pcm, sr = pcm16k(os.path.join(SP, "visit.wav"))
    seconds = len(pcm) / 32000
    print(f"audio: {seconds:.1f}s (source rate {sr} Hz)")
    captions = []
    t0 = time.time()
    headers = {"Origin": ORIGIN, "Cookie": doc_cookie}
    async with websockets.connect(f"{WS}/consultations/{cid}/live", additional_headers=headers, max_size=2**20) as ws:
        async def reader():
            try:
                async for msg in ws:
                    m = json.loads(msg)
                    if m.get("type") == "caption":
                        m["arrived"] = time.time() - t0
                        captions.append(m)
                        print(f"   +{m['arrived']:5.1f}s  [{m['start']:4.1f}-{m['end']:4.1f}] {m['text']}")
            except websockets.ConnectionClosed:
                pass
        rt = asyncio.create_task(reader())
        # malformed frames must be ignored, not fatal
        await ws.send(b"\x01")  # odd length
        await ws.send(b"\x00" * (200 * 1024))  # oversized
        for i in range(0, len(pcm), 32000):  # one-second frames at real-time speed
            await ws.send(pcm[i:i + 32000])
            await asyncio.sleep(1.0)
        await ws.send("end")
        await asyncio.sleep(12)  # let the worker finish the tail
        await ws.close()
        await rt
    text = " ".join(c["text"] for c in captions).lower()
    check("captions arrived while the audio was still streaming", any(c["arrived"] < seconds for c in captions), [round(c["arrived"], 1) for c in captions])
    check("captions are in order (increasing seq)", [c["seq"] for c in captions] == sorted(c["seq"] for c in captions) and len(captions) >= 3, len(captions))
    check("caption text captured the key clinical words (drug names may be misheard live; the accurate transcript fixes them)", "chest pain" in text and "fever" in text and "blood pressure" in text, text[:160])
    check("malformed/oversized frames did not break the stream", len(captions) >= 3)
    # delay of each caption behind the end of the audio it covers
    delays = [c["arrived"] - c["end"] for c in captions if c["end"] <= seconds]
    if delays:
        print(f"   caption delay behind speech: min {min(delays):.1f}s  median {sorted(delays)[len(delays)//2]:.1f}s  max {max(delays):.1f}s")

    print("\n--- consultation is unaffected; the normal Stop + accurate transcript path still works")
    r = doc.post(f"/consultations/{cid}/stop")
    check("stop (no audio) still works after a live session", r.status_code == 200, r.text[:100])
    await expect_close("after Stop the live socket is refused (status no longer in_progress)", doc_cookie, cid, expect=4404)
    print(f"\n{sum(R)}/{len(R)} passed")

asyncio.run(main())
