import os

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse


OLLAMA_LOCAL_URL = os.getenv("OLLAMA_LOCAL_URL", "http://127.0.0.1:11434")
OLLAMA_PROXY_KEY = os.getenv("OLLAMA_PROXY_KEY")

app = FastAPI()


def check_auth(authorization: str | None):
    if not OLLAMA_PROXY_KEY:
        raise HTTPException(status_code=500, detail="OLLAMA_PROXY_KEY non impostata sul proxy")
    expected = f"Bearer {OLLAMA_PROXY_KEY}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Non autorizzato")


async def forward_ollama(path: str, request: Request, authorization: str | None):
    check_auth(authorization)
    body = await request.body()
    headers = {"Content-Type": request.headers.get("content-type", "application/json")}
    target = f"{OLLAMA_LOCAL_URL}{path}"

    client = httpx.AsyncClient(timeout=None)
    upstream = await client.stream("POST", target, content=body, headers=headers).__aenter__()

    async def stream_response():
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        stream_response(),
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@app.get("/")
async def health():
    return {"ok": True, "service": "ollama-proxy"}


@app.post("/api/chat")
async def chat(request: Request, authorization: str | None = Header(default=None)):
    return await forward_ollama("/api/chat", request, authorization)


@app.post("/api/generate")
async def generate(request: Request, authorization: str | None = Header(default=None)):
    return await forward_ollama("/api/generate", request, authorization)
