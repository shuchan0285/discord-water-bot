# main.py
import discord
from discord.ext import commands
import database
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 初始化資料庫
        database.init_db()
        print("資料庫初始化完成")

        # 自動載入 cogs 資料夾底下的所有功能模組
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                # 將檔名轉換為模組路徑 (例如 cogs.water_reminder)
                extension_name = f'cogs.{filename[:-3]}'
                await self.load_extension(extension_name)
                print(f"已載入模組: {extension_name}")

        # 同步斜線指令到 Discord 伺服器
        await self.tree.sync()
        print("斜線指令同步完成")

    async def on_ready(self):
        print(f'Bot 已經成功登入為 {self.user}')

if __name__ == "__main__":
    bot = MyBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ 找不到 DISCORD_TOKEN，請檢查 .env 檔案！")
    else:
        bot.run(token)