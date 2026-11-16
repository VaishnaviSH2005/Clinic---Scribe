# Generates artifacts\visit.wav: a synthesized doctor-patient dialogue (no real patient data).
Add-Type -AssemblyName System.Speech
$dir = Join-Path $PSScriptRoot "artifacts"
New-Item -ItemType Directory -Force $dir | Out-Null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile((Join-Path $dir "visit.wav"))
$s.Rate = -1
$s.Speak("Doctor: Good morning. What brings you in today? Patient: I have had chest pain and shortness of breath for three days. The pain gets worse when I climb stairs. Doctor: Do you have any fever or cough? Patient: No fever, but I feel dizzy sometimes. I take metformin five hundred milligrams twice daily for diabetes. Doctor: Your blood pressure is one fifty over ninety. I will order an ECG and start aspirin seventy five milligrams daily. Please come back in one week.")
$s.Dispose()
"Wrote $(Join-Path $dir 'visit.wav')"
