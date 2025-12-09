from fastapi import FastAPI, Request, HTTPException
import uvicorn
import os
import nacl.signing
import nacl.exceptions
import json
 
PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
 
app = FastAPI()
 
# Discord署名検証
def verify_signature(request: Request, body: bytes):
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
 
    if signature is None or timestamp is None:
        raise HTTPException(status_code=401, detail="Invalid signature headers")
 
    message = timestamp.encode() + body
    verify_key = nacl.signing.VerifyKey(bytes.fromhex(PUBLIC_KEY))
 
    try:
        verify_key.verify(message, bytes.fromhex(signature))
    except nacl.exceptions.BadSignatureError:
        raise HTTPException(status_code=401, detail="Invalid request signature")
 
 
@app.post("/")
async def interactions(request: Request):
    body = await request.body()
    verify_signature(request, body)
 
    data = json.loads(body)
 
    # DiscordのPINGに応答（必須）
    if data["type"] == 1:
        return {"type": 1}
 
    # コマンド応答
    if data["type"] == 2:
        name = data["data"]["name"]
 
        if name == "test":
            return {
                "type": 4,
                "data": {"content": "Cloud Run からの応答に成功！"}
            }
 
    return {"type": 4, "data": {"content": "Unknown command"}}
 
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
uvicorn.run() - Complete Guide
Master uvicorn.run() function for programmatic ASGI server control
 
