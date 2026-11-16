// Real-browser test of live captions (needs: npm i playwright-core, Chrome, the full stack running).
// Real-browser test of live captions: your installed Chrome, fake microphone = the test dialogue WAV.
const { chromium } = require("playwright-core");
const path = require("path");

const SP = path.join(__dirname, "artifacts");
const WAV = path.join(SP, "visit.wav");
const FE = "http://localhost:3000";
const API = "http://localhost:8000/api/v1";
let pass = 0, fail = 0;
const check = (n, c, d = "") => { c ? pass++ : fail++; console.log((c ? "  PASS " : "  FAIL ") + n + (c ? "" : "   <-- " + d)); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: true,
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-audio-capture=${WAV}`, "--autoplay-policy=no-user-gesture-required"],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push("pageerror: " + e.message));
  const sockets = [];
  page.on("websocket", (ws) => {
    const info = { url: ws.url(), sent: 0, sentBytes: 0, received: [], closed: false };
    sockets.push(info);
    ws.on("framesent", (f) => { info.sent++; info.sentBytes += (f.payload ? f.payload.length : 0); });
    ws.on("framereceived", (f) => info.received.push(typeof f.payload === "string" ? f.payload : "<binary>"));
    ws.on("close", () => { info.closed = true; });
  });

  console.log("--- login (real UI)");
  await page.goto(FE + "/login");
  await page.fill("#email", "doctor.cardio@cliniscribe.ai");
  await page.fill("#password", "ChangeMe123!");
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard", { timeout: 30000 });
  check("logged in through the real login form", page.url().includes("/dashboard"), page.url());

  const patients = await (await context.request.get(`${API}/patients`)).json();
  const started = await (await context.request.post(`${API}/consultations/start`, { data: { patient_id: patients.data[0].id, chief_complaint: "BROWSER LIVE-CAPTION TEST" } })).json();
  const cid = started.data.id;
  console.log("consultation", cid);

  console.log("--- open the workspace and record");
  await page.goto(`${FE}/consultations/${cid}`);
  await page.getByRole("button", { name: /start recording/i }).waitFor({ timeout: 60000 });
  await page.screenshot({ path: path.join(SP, "live_1_before.png") });
  await page.getByRole("button", { name: /start recording/i }).click();
  await page.getByRole("button", { name: /stop recording/i }).waitFor({ timeout: 20000 });
  check("recording started (microphone granted, 'Stop recording' visible)", true);

  // watch the transcript card while the fake mic plays the dialogue
  const t0 = Date.now();
  let firstCaptionAt = null, lastText = "";
  for (let i = 0; i < 38; i++) {
    await sleep(1000);
    const txt = await page.locator("[aria-live='polite']").first().innerText().catch(() => "");
    if (txt && txt.trim() && firstCaptionAt === null) { firstCaptionAt = (Date.now() - t0) / 1000; console.log(`   first caption visible after ${firstCaptionAt.toFixed(1)}s`); }
    lastText = txt || lastText;
    if (i === 14) await page.screenshot({ path: path.join(SP, "live_2_during.png") });
  }
  const live = sockets.find((s) => s.url.includes("/live"));
  check("browser opened the live WebSocket", !!live, JSON.stringify(sockets.map((s) => s.url)));
  check("browser streamed audio frames to the server", live && live.sent >= 20 && live.sentBytes > 500000, live && `${live.sent} frames, ${live.sentBytes} bytes`);
  check("captions appeared in the transcript panel while still recording", firstCaptionAt !== null, "none");
  const low = lastText.toLowerCase();
  console.log("   panel text (end of recording):\n     " + lastText.replace(/\n/g, "\n     "));
  check("live text contains the clinical content", low.includes("chest pain") && low.includes("fever"), low.slice(0, 160));
  check("the 'Live' indicator was shown", (await page.getByText("Live", { exact: true }).count()) >= 1);

  console.log("--- stop: the normal recording upload + accurate transcript path must still work");
  await page.getByRole("button", { name: /stop recording/i }).click();
  await page.getByText(/AI is processing the recording/i).waitFor({ timeout: 30000 }).catch(() => {});
  await sleep(1500);
  check("live socket closed after Stop", !!sockets.find((s) => s.url.includes("/live") && s.closed));
  let status = "?";
  for (let i = 0; i < 70; i++) {
    const ws = await (await context.request.get(`${API}/consultations/${cid}`)).json();
    status = ws.data.consultation.status;
    if (status === "pending_review") {
      const segs = (ws.data.transcript.cleaned_transcript || ws.data.transcript.raw_transcript || []);
      check("recording uploaded and accurately transcribed after Stop (final transcript)", segs.length >= 5, segs.length);
      const finalText = segs.map((s) => s.text).join(" ").toLowerCase();
      check("accurate transcript has the drug names live captions can miss", finalText.includes("metformin") && finalText.includes("aspirin"), finalText.slice(0, 120));
      break;
    }
    await sleep(2000);
  }
  check("consultation reached 'pending_review'", status === "pending_review", status);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(SP, "live_3_after.png") });
  const finalPanel = await page.locator("body").innerText().catch(() => "");
  check("final transcript replaced the live preview in the UI", !/Preparing the accurate transcript/i.test(finalPanel) && /Transcript/i.test(finalPanel));

  const bad = consoleErrors.filter((e) => !/favicon|Failed to load resource.*(401|404)|ERR_/i.test(e));
  check("no JavaScript errors in the browser console", bad.length === 0, bad.slice(0, 3).join(" | "));
  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("TEST CRASHED:", e); process.exit(2); });
