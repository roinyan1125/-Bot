import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
import asyncio
from datetime import timedelta

# ログ設定
logging.basicConfig(level=logging.INFO)

# インテントの設定
intents = discord.Intents.default()
intents.members = True

# 作成者のユーザーIDを指定
BOT_OWNER_ID = 1005408303825829998

def create_view(entry):
    view = discord.ui.View(timeout=None)

    async def button_callback(interaction: discord.Interaction):
        guild = interaction.guild
        saved_role = discord.utils.get(guild.roles, id=entry["role_id"])

        if not saved_role:
            await interaction.response.send_message("保存されたロールが見つかりません。", ephemeral=True)
            return

        if saved_role in interaction.user.roles:
            await interaction.response.send_message("すでにそのロールを持っています！", ephemeral=True)
        else:
            await interaction.user.add_roles(saved_role)
            await interaction.response.send_message(f"{saved_role.name} が付与されました！", ephemeral=True)

    button = discord.ui.Button(label="認証する", style=discord.ButtonStyle.green)
    button.callback = button_callback
    view.add_item(button)
    return view

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.saved_data = []  # データ保存用

    async def setup_hook(self):
        await self.tree.sync()
        logging.info("スラッシュコマンドを同期しました。")
        await self.load_data()

    async def load_data(self):
        try:
            if os.path.exists("saved_data.json"):
                with open("saved_data.json", "r", encoding="utf-8") as f:
                    self.saved_data = json.load(f)
                logging.info(f"データをロードしました: {self.saved_data}")
            else:
                logging.info("saved_data.json が存在しません。新規作成します。")
                self.saved_data = []
        except json.JSONDecodeError as e:
            logging.error(f"JSONのデコードエラー: {e}")
            self.saved_data = []
        except Exception as e:
            logging.error(f"データの読み込み中に予期しないエラーが発生しました: {e}")
            self.saved_data = []

    def save_data(self):
        try:
            with open("saved_data.json", "w", encoding="utf-8") as f:
                json.dump(self.saved_data, f, indent=4, ensure_ascii=False)
            logging.info("データを保存しました。")
        except Exception as e:
            logging.error(f"データの保存中にエラーが発生しました: {e}")

    async def on_ready(self):
        logging.info(f"Botがオンライン: {self.user}")
        print(f"{self.user} が準備完了しました！✨")

        channel = self.get_channel(1288625891202568254)  # 通知を送るチャンネルのIDを指定
        if channel:
            await channel.send("Botが起動しました！")
        else:
            print("チャンネルが見つかりませんでした。")

        # 保存されたエントリのビューを再生成
        for entry in self.saved_data:
            guild = self.get_guild(entry["guild_id"])
            if not guild:
                logging.warning(f"ギルドが見つかりません: {entry['guild_id']}")
                continue

            channel = guild.get_channel(entry["channel_id"])
            if not channel:
                logging.warning(f"チャンネルが見つかりません: {entry['channel_id']}")
                continue

            try:
                message = await channel.fetch_message(entry["message_id"])
                view = create_view(entry)
                await message.edit(view=view)
            except discord.errors.NotFound:
                logging.warning(f"保存されたメッセージが見つかりませんでした: {entry['message_id']}")
                embed = discord.Embed(
                    title="認証システム",
                    description="下のボタンを押してロールを取得してください。",
                    color=0x00ff00,
                )
                view = create_view(entry)
                new_message = await channel.send(embed=embed, view=view)
                entry["message_id"] = new_message.id
                self.save_data()

        # ステータス変更ループをバックグラウンドで起動
        self.loop.create_task(self.status_change_loop())

    async def status_change_loop(self):
        while not self.is_closed():
            server_count = len(self.guilds)
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name=f"参加サーバー数: {server_count}"))
            await asyncio.sleep(10)
            latency = round(self.latency * 1000)
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name=f"Ping: {latency}ms"))
            await asyncio.sleep(10)
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name=f"Bot初めて作るからバグが多すぎる"))
            await asyncio.sleep(10)
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name=f"スラッシュコマンド2個のコマンドは使えません"))
            await asyncio.sleep(10)
            await self.change_presence(status=discord.Status.online, activity=discord.Game(name=f"君のことをずっと見ているよ？"))
            await asyncio.sleep(2)

bot = MyBot()

# 以下コマンド定義

@bot.tree.command(name="hello", description="挨拶")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("こんにちは！")

@bot.tree.command(name="ping", description="Botの応答速度を表示します")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Ping: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="help", description="ヘルプを表示します")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Help",
        description="利用できるコマンド一覧:\n- /ping: Ping表示\n- /hello: 挨拶\n- /help: ヘルプを表示",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="チャンネルから指定した数のメッセージを削除します。")
@app_commands.describe(number_of_messages="削除するメッセージの数（正の数）を入力してください。")
async def clear(interaction: discord.Interaction, number_of_messages: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("⛔ 権限が必要です。", ephemeral=True)
        return
    if number_of_messages < 1:
        await interaction.response.send_message("⚠️ 正の数を指定してください。", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=number_of_messages)
        await interaction.followup.send(f"✅ {len(deleted)} 件削除しました。", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ エラー: {e}", ephemeral=True)

@bot.tree.command(name="authenticate_user", description="指定されたロールを付与します")
@app_commands.describe(role="付与したいロールを選択してください")
async def authenticate_user(interaction: discord.Interaction, role: discord.Role):
    # 作成者のみ使用可能に制限
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("⛔ このコマンドは作成者のみ使用可能です。", ephemeral=True)
        return

    embed = discord.Embed(title="認証システム", description="下のボタンを押してロールを取得してください。", color=0x00ff00)
    entry = {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id, "message_id": None, "role_id": role.id}
    view = create_view(entry)
    message = await interaction.response.send_message(embed=embed, view=view)
    entry["message_id"] = message.id
    bot.saved_data.append(entry)
    bot.save_data()

@bot.tree.command(name="timeout", description="指定した複数のユーザーをタイムアウトします。")
@app_commands.describe(
    d="タイムアウト日数を入力してください（0も入力可能）。",
    h="タイムアウト時間を入力してください（0も入力可能）。",
    m="タイムアウト分を入力してください（0も入力可能）。",
    s="タイムアウト秒を入力してください（0も入力可能）。",
    user1="タイムアウトする最初のユーザー。",
    user2="タイムアウトする2番目のユーザー。",
    user3="タイムアウトする3番目のユーザー。",
    user4="タイムアウトする4番目のユーザー。",
    user5="タイムアウトする5番目のユーザー。",
    user6="タイムアウトする6番目のユーザー。",
    user7="タイムアウトする7番目のユーザー。",
    user8="タイムアウトする8番目のユーザー。",
    user9="タイムアウトする9番目のユーザー。",
    user10="タイムアウトする10番目のユーザー。"
)
async def timeout(
    interaction: discord.Interaction,
    d: int,
    h: int,
    m: int,
    s: int,
    user1: discord.Member = None,
    user2: discord.Member = None,
    user3: discord.Member = None,
    user4: discord.Member = None,
    user5: discord.Member = None,
    user6: discord.Member = None,
    user7: discord.Member = None,
    user8: discord.Member = None,
    user9: discord.Member = None,
    user10: discord.Member = None
):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("⛔ 権限が必要です。", ephemeral=True)
        return
    duration = timedelta(days=d, hours=h, minutes=m, seconds=s)
    if duration.total_seconds() <= 0:
        await interaction.response.send_message("⛔ 時間を正しく指定してください。", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    users = [u for u in (user1, user2, user3, user4, user5, user6, user7, user8, user9, user10) if u]
    results = []
    for user in users:
        try:
            await user.timeout(duration)
            time_string = f"{d}日 {h}時間 {m}分 {s}秒"
            results.append(f"✅ {user.mention} を {time_string} タイムアウトしました。")
        except Exception as e:
            results.append(f"⛔ {user.mention} のタイムアウトに失敗: {e}")
    await interaction.followup.send("\n".join(results), ephemeral=True)

@bot.tree.command(name="serverinfo", description="サーバーの情報を確認できます。")
async def serverinfo(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ 管理者権限が必要です。", ephemeral=True)
        return

    guild = interaction.guild
    roles = [role for role in guild.roles]
    text_channels = [channel for channel in guild.text_channels]
    bot_count = sum(1 for member in guild.members if member.bot)
    member_count = guild.member_count - bot_count
    embed = discord.Embed(title=f"{guild.name} info", color=0x3683ff)
    embed.add_field(name="管理者", value=f"{guild.owner.mention}", inline=False)
    embed.add_field(name="ID", value=f"{guild.id}", inline=False)
    embed.add_field(name="チャンネル数", value=f"{len(text_channels)}", inline=False)
    embed.add_field(name="ロール数", value=f"{len(roles)}", inline=False)
    embed.add_field(name="サーバーブースター", value=f"{guild.premium_subscription_count}", inline=False)
    embed.add_field(name="メンバー数", value=f"{member_count}", inline=False)
    embed.add_field(name="Bot数", value=f"{bot_count}", inline=False)
    embed.add_field(name="メンバー・bot合計", value=f"{guild.member_count}", inline=False)
    embed.add_field(name="サーバー設立日", value=f"{guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}", inline=False)
    embed.set_footer(text=f"実行者: {interaction.user}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="ユーザーの情報を確認できます。")
@app_commands.describe(user="情報を取得したいユーザーを指定してください（省略すると実行者の情報を表示します）")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ 管理者権限が必要です。", ephemeral=True)
        return

    if user is None:
        user = interaction.user
    embed = discord.Embed(title=f"user {user.name}", description="userinfo", color=0x3683ff)
    embed.add_field(name="名前", value=f"{user.mention}", inline=False)
    embed.add_field(name="ID", value=f"{user.id}", inline=False)
    embed.add_field(name="ACTIVITY", value=f"{user.activity}", inline=False)
    embed.add_field(name="TOP_ROLE", value=f"{user.top_role}", inline=False)
    embed.add_field(name="discriminator", value=f"#{user.discriminator}", inline=False)
    embed.add_field(name="サーバー参加", value=f"{user.joined_at.strftime('%Y-%m-%d %H:%M:%S')}" if user.joined_at else "不明", inline=False)
    embed.add_field(name="アカウント作成", value=f"{user.created_at.strftime('%Y-%m-%d %H:%M:%S')}", inline=False)
    embed.set_thumbnail(url=f"{user.avatar.url}")
    embed.set_footer(text=f"実行者 : {interaction.user}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leave", description="Botを指定したサーバーから退出させます。")
@app_commands.describe(
    server_id="退出するサーバーのIDを入力してください（最大25桁まで）。"
)
async def leave(interaction: discord.Interaction, server_id: str):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            "⛔ このコマンドを使用できるのはBotの作成者のみです。", ephemeral=True
        )
        return

    if not server_id.isdigit() or len(server_id) > 25:
        await interaction.response.send_message(
            "⛔ サーバーIDは有効な数字で、25桁以内で入力してください。", ephemeral=True
        )
        return

    server = bot.get_guild(int(server_id))
    if server is None:
        await interaction.response.send_message(
            "指定されたサーバーが見つかりませんでした。", ephemeral=True
        )
        return

    await server.leave()
    await interaction.response.send_message(
        f"✅ サーバーから退出しました: {server.name}", ephemeral=True
    )

@bot.tree.command(name="embed", description="埋め込みメッセージを作成します")
@app_commands.describe(
    title="タイトルを入力してください。",
    description="文字を入力してください（改行は \\n を使用）。",
    color="カラーコードを入力してください（例: #5865F2）。"
)
async def embed(
    interaction: discord.Interaction, 
    title: str, 
    description: str, 
    color: str = None
):
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "⛔ このコマンドは管理者のみ実行可能です。",
            ephemeral=True  # エラー表示をユーザーにのみ見えるようにする
        )
        return

    # デフォルトの色を設定
    try:
        color_int = int(color.strip('#'), 16) if color else 0x5865F2  # カラーコードの整形
    except ValueError:
        await interaction.response.send_message(
            "⚠️ 無効なカラーコードが入力されました。例: #5865F2 を使用してください。",
            ephemeral=True
        )
        return

    description = description.replace('\\n', '\n')  # 改行文字の置換

    # 埋め込みメッセージ作成
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color(color_int)
    )
    
    await interaction.response.send_message(embed=embed)

from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='ja')

@bot.tree.context_menu(name="日本語翻訳")
async def translate_message(interaction: discord.Interaction, message: discord.Message):
    try:
        translation = translator.translate(message.content)
        response = f"**翻訳**: {translation}\n> **-# 実行: {interaction.user.display_name}**"
        await interaction.response.send_message(response)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@bot.tree.command(name="stop", description="Botを停止します。")
async def stop(interaction: discord.Interaction):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("⛔ このコマンドは作成者のみ使用可能です。", ephemeral=True)
        return

    await interaction.response.send_message("✅ Botを停止します。")
    await bot.close()

# Botの起動
bot.run("MTMzMTExNjUxMzUxMTM0NjI0Ng.GsmnxP.UP3i0i91h5ohy_967APgjYtjEjQ_YVz-3WvnPQ")
