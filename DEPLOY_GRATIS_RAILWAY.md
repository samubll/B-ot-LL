# Deploy gratis con Railway + Ollama sul tuo PC

Railway puo hostare il bot Discord, ma Qwen 14B deve girare sul tuo PC con Ollama.
Per collegarli gratis si usa un tunnel verso un piccolo proxy locale protetto da password.

## 1. Sul tuo PC

Apri PowerShell nella cartella del bot:

```powershell
cd "C:\Users\Samu.DESKTOP-VJ74SBC\OneDrive\Desktop\bot"
```

Avvia Ollama e assicurati che il modello esista:

```powershell
ollama list
```

Imposta una chiave segreta lunga:

```powershell
$env:OLLAMA_PROXY_KEY="cambia-questa-password-con-una-lunga"
```

Avvia il proxy locale:

```powershell
.\start_local_ai_proxy.ps1
```

In un secondo PowerShell avvia il tunnel:

```powershell
.\start_cloudflare_quick_tunnel.ps1
```

Copia l'URL `https://...trycloudflare.com` che appare nel terminale.

## 2. Su Railway

Nel servizio del bot aggiungi queste variabili:

```text
DISCORD_TOKEN=il-token-del-bot-discord
AI_MODEL=qwen2.5:14b
OLLAMA_HOST=https://URL-DEL-TUNNEL.trycloudflare.com
OLLAMA_API_KEY=la-stessa-password-di-OLLAMA_PROXY_KEY
```

Poi fai deploy.

## Limite della soluzione gratis

Il PC deve restare acceso, Ollama deve restare avviato, il proxy deve restare aperto e il tunnel deve restare aperto.
Con il tunnel rapido gratuito l'URL cambia quando lo riavvii, quindi va aggiornato su Railway.

Per un URL fisso gratuito puoi creare un Cloudflare Tunnel nel tuo account Cloudflare Free.
