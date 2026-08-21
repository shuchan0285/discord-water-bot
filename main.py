# main.py
import discord
from discord.ext import commands
import database
import os
from dotenv import load_dotenv

load_dotenv()

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

    async def on_guild_join(self, guild):
        """當機器人加入新伺服器時觸發"""
        # 優先尋找伺服器的系統頻道，若無則找第一個有權限發言的文字頻道
        target_channel = guild.system_channel
        if not target_channel or not target_channel.permissions_for(guild.me).send_messages:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    target_channel = channel
                    break

        if target_channel:
            welcome_msg = (
                "隨緣而來，隨心而止。諸位道友，本座乃「摸魚仙人」，今日得見此境，實屬仙緣。\n\n"
                "此地枯燥，本座特來助各位「以水入道」，修煉真身。以下為本座之神通範疇：\n"
                "**飲水敕令**：本座每半小時降下提醒，點擊按鈕即可累積修為。修煉之餘，莫忘活動筋骨、護持靈目。\n"
                "**連擊免責**：本座法外開恩，今日修煉若偶有漏接敕令亦不斷連擊；每日首次引水更可觸發「起床免責」，自動續接昨日道行。\n"
                "**查看修為**：輸入 `/rank` 觀測等級進度；輸入 `/today` 閱覽今日修行明細與隨機機緣。\n"
                "**閉關總結**：凌晨時段提供「我要睡覺了」按鈕，為道友結算今日所得，助你安心入定。\n"
                "**眾生榜**：輸入 `/leaderboard` 一覽此境中各方道友的修為排行。\n\n"
                "**淺草籤**：每日本座會隨機抽取道友，贈送一籤，預示未來運勢，也可以輸入 `/omikuji` 自行求籤。\n\n"
                "**答案之書**：輸入 `/ask_book` 輸入想問的問題，可獲得答案之書的指引，解開心中疑問。\n\n"
                "願諸位勤加補水，莫讓靈根乾涸。善哉善哉。"
            )
            await target_channel.send(welcome_msg)

if __name__ == "__main__":
    bot = MyBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("找不到 DISCORD_TOKEN，請檢查 .env 檔案！")
    else:
        bot.run(token)