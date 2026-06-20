$ErrorActionPreference = "Stop"

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "cloudflared non trovato."
    Write-Host "Installalo gratis da: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    Write-Host "Oppure, se hai winget:"
    Write-Host "winget install --id Cloudflare.cloudflared"
    exit 1
}

cloudflared tunnel --url http://127.0.0.1:8000
