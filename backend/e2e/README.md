# End-to-end test (A to Z)

`run_e2e.py` drives the **live local stack** through every role and module
(~200 checks). Claude is replaced by `fake_claude.py`, a tiny local stand-in that
speaks the Anthropic API, so the AI-generation pipeline is exercised end to end
without a real API key. (It proves the integration, not the quality of real Claude
output.)

## Run it

```powershell
# 1. infrastructure + apps (see the main README): Postgres, Redis, Mailpit, API :8000, frontend :3000
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis mailpit

# 2. test audio (synthesized speech, no real patient data)
powershell -ExecutionPolicy Bypass -File backend\e2e\make_test_audio.ps1

# 3. stand-in Claude + an AI worker that uses it (stop your normal worker first)
python backend\e2e\fake_claude.py                      # terminal A  (listens on 127.0.0.1:8765)
$env:ANTHROPIC_BASE_URL="http://127.0.0.1:8765"; $env:CLAUDE_API_KEY="fake-test-key"
python -m app.workers.pipeline_worker                    # terminal B  (from backend/)

# 4. run
python backend\e2e\run_e2e.py                           # terminal C
```

The suite needs the demo seed data (`doctor.cardio@cliniscribe.ai` etc., password
`ChangeMe123!`) and reads invitation / reset emails from Mailpit
(http://localhost:8025). It creates "E2E Hospital ..." data; remove it afterwards if
you do not want it.

## Live captions tests

- `live_ws_test.py` - streams `artifacts/visit.wav` over the live WebSocket at real-time speed and
  checks security (no cookie, wrong role, other doctor, foreign Origin), caption order and delay.
  Needs the API, Redis and `python -m app.workers.live_worker`.
- `browser_live.js` - drives your installed Chrome with the same WAV as a fake microphone, through
  the real login form and workspace UI (`npm i playwright-core` somewhere outside the project, then
  `node backend/e2e/browser_live.js`; set `CHROME_PATH` if Chrome is installed elsewhere).
