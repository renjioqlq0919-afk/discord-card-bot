import discord

import os

import logging

from http.server import BaseHTTPRequestHandler, HTTPServer

import threading

import asyncio

import sys

import json

from firebase_admin import initialize_app, firestore, credentials
 
# ロガー設定

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
 
# --- グローバル変数 ---

# Firestoreインスタンスの初期化を試みる

db = None

try:

    # Canvas環境からFirebase設定を取得

    firebase_config_str = os.getenv('__firebase_config')

    app_id = os.getenv('__app_id')
 
    if firebase_config_str:

        firebase_config = json.loads(firebase_config_str)

        # Firebase Admin SDKはJSON設定ではなく、クレデンシャルオブジェクトが必要です

        # Cloud Run環境では、Google Application Default Credentials (ADC)が自動的に使用されます。

        # サービスの初期化に必要なのはプロジェクトIDのみです。

        if 'projectId' in firebase_config:

            cred = credentials.ApplicationDefault()

            # 環境変数 'GCLOUD_PROJECT' または 'GOOGLE_CLOUD_PROJECT' を確認し、自動認証を信頼します。

            # ADCが利用できない場合、Botはクラッシュします。

            initialize_app(cred, {'projectId': firebase_config['projectId']})

            db = firestore.client()

            logger.info("Firestore client initialized successfully using ADC.")

        else:

            logger.error("Firebase config is missing 'projectId'. Cannot initialize Firestore.")

    else:

        logger.warning("Firebase config is not available. Running without database persistence.")

except Exception as e:

    logger.error(f"Failed to initialize Firebase/Firestore: {e}")

    # dbがNoneのままになる
 
# --- Health Check Server ---

class HealthCheckHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == '/healthz':

            self.send_response(200)

            self.end_headers()

            self.wfile.write(b"OK")

        else:

            self.send_response(404)

            self.end_headers()
 
def run_web_server():

    server_address = ('0.0.0.0', 8080)

    httpd = HTTPServer(server_address, HealthCheckHandler)

    logger.info("HTTP server running on port 8080 for health check.")

    httpd.serve_forever()

# --------------------------
 
# --- Bot Execution ---

async def start_bot(bot, token):

    try:

        await bot.start(token)

    except discord.errors.LoginFailure as e:

        logger.error(f"Bot failed to run: {e}")

        logger.fatal("FATAL ERROR: Discordトークンが規定値です。環境変数をチェックしてください。")

        sys.exit(1)

    except Exception as e:

        logger.error(f"An unexpected error occurred: {e}")

        sys.exit(1)
 
 
def run_bot():

    token = os.getenv('DISCORD_TOKEN')

    if not token:

        logger.error("DISCORD_TOKEN environment variable not set.")

        sys.exit(1) 

    token_len = len(token)

    token_start = token[:5] if token_len > 5 else token

    token_end = token[-5:] if token_len > 5 else token

    logger.info(f"Token Check: Length={token_len}, Start='{token_start}', End='{token_end}'")
 
    if token_len < 30:

        logger.error(f"Invalid token length ({token_len}).")

        sys.exit(1)
 
    intents = discord.Intents.default()

    intents.members = True

    intents.message_content = True
 
    bot = discord.Client(intents=intents)

    tree = discord.app_commands.CommandTree(bot)
 
    @bot.event

    async def on_ready():

        logger.info(f'logged in as {bot.user} (ID: {bot.user.id})')

        try:

            await tree.sync() 

            logger.info("Application commands synced globally.")

        except Exception as e:

            logger.error(f"Failed to sync commands: {e}")

        logger.info('Bot is ready. (オンライン状態維持中)')
 
 
    @tree.command(name='card', description='趣味の募集カードを作成し、データベースに保存します')

    async def make_card(interaction: discord.Interaction, title: str, description: str):

        """趣味の募集カードを作成し、Firestoreに保存するスラッシュコマンド。"""

        # 1. Discordへの応答 (見た目のカード生成)

        embed = discord.Embed(

            title=f"募集: {title}", 

            description=description, 

            color=discord.Color.blue()

        )

        embed.set_author(name=f"募集者: {interaction.user.display_name}")

        # 2. データベースへの保存

        db_success = False

        if db:

            # Firestoreに保存するデータ構造を定義

            card_data = {

                'title': title,

                'description': description,

                'user_id': str(interaction.user.id),

                'user_name': interaction.user.display_name,

                'channel_id': str(interaction.channel_id),

                'server_id': str(interaction.guild_id),

                'created_at': firestore.SERVER_TIMESTAMP # サーバー側でタイムスタンプを生成

            }

            # Firestoreのコレクションパスを定義 (パブリックデータとして保存)

            # /artifacts/{appId}/public/data/cards/{documentId}

            collection_path = f"artifacts/{app_id}/public/data/cards"

            try:

                # Firestoreは非同期ではないため、同期的に処理

                doc_ref = db.collection(collection_path).add(card_data)

                logger.info(f"Card saved to Firestore: {doc_ref[1].id}")

                db_success = True

            except Exception as e:

                logger.error(f"Firestore save failed: {e}")

                # データベース保存失敗時のメッセージを生成

                error_msg = f"⚠️ データベースへの保存に失敗しました。\n詳細: {e}"

                embed.add_field(name="保存エラー", value=error_msg, inline=False)
 
 
        # 3. ユーザーへの最終応答

        await interaction.response.send_message(embed=embed)

        # データベース保存成功時の確認メッセージをBotの応答とは別に送信

        if db_success:

            success_message = "✅ 募集カードはデータベースに保存されました！他のユーザーと共有できます。"

            await interaction.followup.send(success_message, ephemeral=True) # 実行者のみに見えるメッセージ

        elif not db:

             await interaction.followup.send(

                 "⚠️ データベース接続が未初期化です。カードは一時的なものであり、保存されません。", 

                 ephemeral=True

             )

        logger.info(f"Card command executed by {interaction.user.name}. DB Success: {db_success}")
 
 
    # /list コマンドの仮実装 (未実装)

    @tree.command(name='list', description='募集中のカードを一覧表示します (未実装)')

    async def list_cards(interaction: discord.Interaction):

        await interaction.response.send_message("このコマンドは現在開発中です！", ephemeral=True)
 
 
    http_thread = threading.Thread(target=run_web_server, daemon=True)

    http_thread.start()

    logger.info("Starting Discord Bot in the main thread...")

    asyncio.run(start_bot(bot, token))
 
 
if __name__ == '__main__':

    try:

        run_bot()

    except Exception as e:

        logger.error(f"Main execution failed with unexpected error: {e}")

        sys.exit(1)

    logger.info("Bot execution finished.")

    sys.exit(0)
 