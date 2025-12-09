import os
import asyncio
from fastapi import FastAPI
import uvicorn
import discord
from discord.ext import commands
 
# ===== Discord Bot 設定 =====
TOKEN = os.getenv("DISCORD_TOKEN")  # Cloud Run に環境変数でセット
INTENTS = discord.Intents.default()
INTENTS.message_content = True
 
bot = commands.Bot(command_prefix="!", intents=INTENTS)
 
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
 
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")
 
# ===== Web サーバー (Cloud Run 用) =====
app = FastAPI()
 
@app.get("/")
def root():
    return {"status": "Bot is running on Cloud Run!"}
 
# ===== Discord Bot と Web サーバーを同時に実行する =====
async def start_bot():
    """Discord Bot を非同期で起動"""
    await bot.start(TOKEN)
 
async def start_web():
    """FastAPI を Cloud Run のポートで起動"""
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
 
async def main():
    # discord bot と web server を並列実行
    await asyncio.gather(
        start_bot(),
        start_web(),
    )
 
if __name__ == "__main__":
    asyncio.run(main())
 
