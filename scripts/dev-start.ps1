<#
  Starts the full CliniScribe AI stack for local development on Windows:
    Postgres + Redis (Docker) -> DB migrations -> API (:8000) -> AI worker -> Frontend (:3000)

  Usage (from the repo root):   powershell -ExecutionPolicy Bypass -File scripts\dev-start.ps1
  Safe to re-run: anything already listening on its port is left alone.
  Prerequisites: Docker Desktop running, backend\.venv created, frontend deps installed (pnpm install).
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$py = Join-Path $backend ".venv\Scripts\python.exe"

function Test-Port([int]$port) {
  [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

if (-not (Test-Path $py)) { throw "backend\.venv not found. Create it: python -m venv backend\.venv; backend\.venv\Scripts\pip install -r backend\requirements.txt -r ai-services\requirements.txt" }
if (-not (Test-Path (Join-Path $backend ".env"))) { throw "backend\.env missing. Copy backend\.env.example to backend\.env and fill it in." }

Write-Host "1/6 Postgres + Redis (Docker)..." -ForegroundColor Cyan
docker compose -f (Join-Path $root "infrastructure\docker\docker-compose.yml") up -d postgres redis mailpit
for ($i = 0; $i -lt 30; $i++) {
  $unhealthy = docker ps --filter "name=cliniscribe-ai" --format "{{.Status}}" | Where-Object { $_ -notmatch "healthy" -or $_ -match "unhealthy|starting" }
  if (-not $unhealthy) { break }
  Start-Sleep -Seconds 2
}

Write-Host "2/6 Database migrations (alembic upgrade head)..." -ForegroundColor Cyan
Push-Location $backend
& $py -m alembic upgrade head
Pop-Location

Write-Host "3/6 API on :8000..." -ForegroundColor Cyan
if (-not (Test-Port 8000)) {
  Start-Process powershell -WorkingDirectory $backend -ArgumentList "-NoExit", "-Command", "& '$py' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
} else { Write-Host "   already running" }

Write-Host "4/6 AI pipeline worker..." -ForegroundColor Cyan
$worker = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match "pipeline_worker" }
if (-not $worker) {
  Start-Process powershell -WorkingDirectory $backend -ArgumentList "-NoExit", "-Command", "& '$py' -m app.workers.pipeline_worker"
} else { Write-Host "   already running" }

Write-Host "5/6 Live caption worker..." -ForegroundColor Cyan
$live = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match "live_worker" }
if (-not $live) {
  Start-Process powershell -WorkingDirectory $backend -ArgumentList "-NoExit", "-Command", "& '$py' -m app.workers.live_worker"
} else { Write-Host "   already running" }

Write-Host "6/6 Frontend on :3000..." -ForegroundColor Cyan
if (-not (Test-Port 3000)) {
  Start-Process powershell -WorkingDirectory $frontend -ArgumentList "-NoExit", "-Command", "pnpm dev"
} else { Write-Host "   already running" }

Write-Host ""
Write-Host "Ready:  http://localhost:3000   (API docs: http://localhost:8000/docs, mail: http://localhost:8025)" -ForegroundColor Green
Write-Host "Demo logins (password ChangeMe123! unless changed): doctor.cardio@cliniscribe.ai, hospital.admin@cliniscribe.ai, receptionist@cliniscribe.ai, superadmin@cliniscribe.ai"
if (-not (Select-String -Path (Join-Path $backend ".env") -Pattern "^CLAUDE_API_KEY=.+" -Quiet)) {
  Write-Host "WARNING: CLAUDE_API_KEY is empty - transcription works, but SOAP / summary / recommendations will fail until it is set in backend\.env." -ForegroundColor Yellow
}
