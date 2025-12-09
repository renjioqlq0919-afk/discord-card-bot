from fastapi import FastAPI, Request, HTTPException
from discord_interactions import verify_key_decorator, InteractionType, InteractionResponseType
import os
 
app = FastAPI()
 
PUBLIC_KEY = os.getenv("PUBLIC_KEY")  # Cloud Run の環境変数に設定する
 
@app.get("/")
def root():
    return {"status": "ok"}
 
@app.post("/interactions")
@verify_key_decorator(PUBLIC_KEY)
async def interactions(request: Request):
    body = await request.json()
 
    # PING に対する応答（Discord がエンドポイント検証で送る）
    if body["type"] == InteractionType.PING:
        return {"type": InteractionResponseType.PONG}
 
    # スラッシュコマンド処理（例：/test）
    if body["type"] == InteractionType.APPLICATION_COMMAND:
        name = body["data"]["name"]
 
        if name == "test":
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": "テスト成功！Cloud Run のエンドポイントは正常です 🎉"
                }
            }
 
    # それ以外（未対応のコマンドなど）
    return {
        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        "data": {"content": "未対応のコマンドです。"}
    }
 
