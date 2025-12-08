import os
import discord
from discord.ext import commands
import asyncio
from aiohttp import web
 
# ====== Discord Token ======
TOKEN = os.environ.get("DISCORD_TOKEN")
 
if TOKEN is None:
    raise RuntimeError("ERROR: 環境変数 DISCORD_TOKEN が設定されていません。")
 
 
# ====== Discord Bot 設定 ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
 
 
# ====== Bot の準備完了イベント ======
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
 
 
# ====== テストコマンド ======
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")
 
 
# ====== Cloud Run 用 HTTP サーバー ======
async def handle(request):
    return web.Response(text="Bot is running!")
 
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
 
    runner = web.AppRunner(app)
    await runner.setup()
 
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
 
    print(f"HTTP server started on port {port}")
 
 
# ====== Bot と Web サーバーを同時起動 ======
async def main():
    # 並列で起動
    await asyncio.gather(
        start_web_server(),
        bot.start(TOKEN)
    )
 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
 
