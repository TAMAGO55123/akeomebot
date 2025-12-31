import discord
from discord.ext import commands, tasks
from discord import app_commands
from os import getenv
import json
import sqlite3
from dotenv import load_dotenv
from logging import DEBUG
from log import get_log, stream_handler
from typing import Union
import datetime
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

log = get_log("Main")

@bot.event
async def on_ready():
    print(f"{bot.user}としてログインしました！")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました！")
    except Exception as e:
        log.error(f"コマンドの同期中にエラーが発生しました。\n{e}")


class serv:
    def __init__(self) -> None:
        DB_FILE = "server.db"
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        # テーブルの作成
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS eco (
                id INTEGER,
                author_id INTEGER,
                timestamp INTEGER
            )
        ''')
        self.conn.commit()
    def get_server(self, server_id:int):
        self.cursor.execute('SELECT author_id, timestamp FROM server WHERE id = ?', (server_id,))
        result = self.cursor.fetchall()
        return result
    def update_user(self, server_id:int, author_id:int, timestamp:float):
        self.cursor.execute("SELECT timestamp FROM server WHERE id = ? AND author_id = ?",(server_id, author_id))
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute('UPDATE server SET timestamp = ? WHERE id = ? AND author_id = ?', (timestamp, server_id, author_id))
        else:
            self.cursor.execute('INSERT INTO server (id, author_id, timestamp) VALUES (?, ?, ?)', (server_id, author_id, timestamp))
        self.conn.commit()

@bot.event
async def on_message(message:discord.Message):
    server_id = message.guild.id
    user_id = message.author.id
    created = message.created_at
    timestamp = created.timestamp()
    _serv = serv()
    if "あけおめ" in message.content:
        _serv.update_user(
            server_id=server_id,
            author_id=user_id,
            timestamp=timestamp
        )
    await bot.process_commands(message)

@bot.tree.command(name="get_time", description="ランキングを作成します。")
async def get_time(interaction:discord.Interaction):
    _serv = serv()
    res = _serv.get_server(interaction.guild.id)
    if res:
        print(res)
        js:list[dict[str, int]] = []
        for i in res:
            time = datetime.datetime.fromtimestamp(i[1])
            jone = datetime.datetime(year=2026, month=1, day=1,hour=0, minute=0, second=0)
            js.append({"id":interaction.guild.id, "author_id":i[0], "timestamp":datetime.datetime.timestamp(time)-datetime.datetime.timestamp(jone)})
        times:list[dict[str, Union[int, float]]] = sorted(js, key=lambda x:abs(x["timestamp"]))
        print(times)
        string = ""
        rank = 0
        for i in times:
            rank += 1
            user = interaction.guild.get_member(i["author_id"])
            string += f"**{rank}位: <@{user.id}>**\n{i["timestamp"]}秒\n"
        await interaction.response.send_message(embed=discord.Embed(
            title="ランキング",
            description=string
        ))
    else:
        await interaction.response.send_message("データがありません")




try:
    bot.run(getenv("TOKEN"), log_handler=stream_handler)
except KeyboardInterrupt:
    raise