$ErrorActionPreference = "Stop"

if (-not $env:OLLAMA_PROXY_KEY) {
    Write-Host "Imposta prima una chiave segreta, per esempio:"
    Write-Host '$env:OLLAMA_PROXY_KEY="scrivi-qui-una-password-lunga"'
    exit 1
}

py -m pip install -r "$PSScriptRoot\requirements-proxy.txt"
py -m uvicorn ollama_proxy:app --host 127.0.0.1 --port 8000
