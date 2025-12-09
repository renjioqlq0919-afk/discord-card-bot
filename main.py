import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
 
app = FastAPI()
 
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
if not DISCORD_PUBLIC_KEY:
    raise ValueError("DISCORD_PUBLIC_KEY is not set in environment variables")
 
# ---- Discord Signature Verification ----
def verify_signature(request: Request, body: bytes):
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
 
    if signature is None or timestamp is None:
        return False
 
    import nacl.signing
    import nacl.exceptions
 
    try:
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
        return True
    except nacl.exceptions.BadSignatureError:
        return False
 
 
# ---- Discord Interactions Endpoint ----
@app.post("/interactions")
async def interactions(request: Request):
    body = await request.body()
 
    if not verify_signature(request, body):
        return JSONResponse(content={"error": "invalid request signature"}, status_code=401)
 
    data = json.loads(body)
 
    # ① PING (Discord がURL検証で送ってくる)
    if data["type"] == 1:
        return JSONResponse(content={"type": 1})
 
    # ② Slash Command の処理
    if data["type"] == 2:  # APPLICATION_COMMAND
        cmd = data["data"]["name"]
 
        if cmd == "hello":
            return JSONResponse(content={
                "type": 4,
                "data": {
                    "content": "Hello from Cloud Run!"
                }
            })
 
    return JSONResponse(content={"type": 4, "data": {"content": "Unknown command"}})
 
 
@app.get("/")
def health():
    return {"status": "ok"}
 
 
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run 必須
    uvicorn.run(app, host="0.0.0.0", port=port)
uvicorn.run() - Complete Guide
Master uvicorn.run() function for programmatic ASGI server control
 
