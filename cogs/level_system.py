import discord
from discord.ext import tasks,commands
from discord import app_commands
import database
import datetime
from constants import TITLE_DATA, ROLE_MAPPING
import os

# ==========================================
# 專屬於 /rank 指令的按鈕面板
# ==========================================
class ResetLevelView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(label="重設等級 (歸零)", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ 你只能重設你自己的等級！", ephemeral=True)
            return
        
        database.reset_user_exp(interaction.user.id)
        
        for child in self.children:
            child.disabled = True
        
        embed = interaction.message.embeds[0]
        embed.description = "⚠️ **此帳號的等級與經驗值已成功歸零。**\n請重新開始你的喝水旅程！"
        embed.color = 0xED4245
        
        await interaction.response.edit_message(embed=embed, view=self)

# ==========================================
# 等級與排行榜系統 (此為 Cog 類別)
# ==========================================
class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        default_id = os.getenv("DEFAULT_CHANNEL_ID")
        channel_id_str = database.get_setting("target_channel_id", default=default_id)
        self.target_channel_id = int(channel_id_str) if channel_id_str else 0
        self.daily_leaderboard_task.start()

    def cog_unload(self):
        self.daily_leaderboard_task.cancel()

    # ==========================================
    # 定時任務：台灣時間每天 23:59 發送排行榜
    # ==========================================
    tz = datetime.timezone(datetime.timedelta(hours=8))
    trigger_time = datetime.time(hour=23, minute=59, tzinfo=tz)

    @tasks.loop(time=trigger_time)
    async def daily_leaderboard_task(self):
        current_id = database.get_setting("target_channel_id", default=os.getenv("DEFAULT_CHANNEL_ID"))
        self.target_channel_id = int(current_id) if current_id else self.target_channel_id

        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            print("排行榜任務找不到指定的頻道！")
            return

        # 1. 取得今日榜首
        top_gainer = database.get_daily_top_gainer()
        
        # 2. 取得總排行榜 (前 10 名)
        data = database.get_participants_paged(10, 0)
        if not data and not top_gainer: 
            return

        # 🌟 修正點：在這裡給予 description 一段初始文字，這樣它就不會是 None 了
        embed = discord.Embed(
            title="🌙 摸魚仙人結算：今日飲水修煉總結", 
            description="一日將盡，本座特此公告今日修為精進之名單。善哉善哉。\n",
            color=0x7289da,
            timestamp=datetime.datetime.now()
        )

        # 3. 今日進步最快區塊
        if top_gainer:
            u_id, daily_val = top_gainer
            guild = channel.guild
            member = guild.get_member(int(u_id))
            name = member.display_name if member else f"隱世道友({u_id})"
            embed.add_field(
                name="🚀 今日進步最快 (今日榜首)",
                value=f"恭喜 **{name}** 今日精進了 **{daily_val}** 點修為！",
                inline=False
            )

        # 4. 組合總榜文字
        leaderboard_text = "\n### 📜 總修為排行\n"
        for i, (u_id, total_exp) in enumerate(data, start=1):
            level, _, _ = database.get_level_info(total_exp)
            role_id = ROLE_MAPPING.get(level)
            title_info = TITLE_DATA.get(level)
            fallback_title = title_info["title"] if title_info else "未知領域"
            display_title = f"<@&{role_id}>" if role_id else f"【{fallback_title}】"
            
            # 確保從伺服器取得成員物件
            guild = channel.guild
            member = guild.get_member(int(u_id))
            name = member.display_name if member else f"隱世道友({u_id})"
            
            if i == 1: rank_icon = "🥇"
            elif i == 2: rank_icon = "🥈"
            elif i == 3: rank_icon = "🥉"
            else: rank_icon = f"` {i} `"
            
            leaderboard_text += f"{rank_icon} **Lv.{level}** {display_title} **{name}** (總經驗: {total_exp})\n"

        # 🌟 這裡使用 += 就不會報錯了，因為前面已經有了仙人的開場白
        embed.description += leaderboard_text
        embed.set_footer(text="明日卯時，再行補水。")
        
        # 5. 發送並重設
        await channel.send(embed=embed)
        database.reset_daily_exp() # 結算後歸零今日經驗

    @daily_leaderboard_task.before_loop
    async def before_leaderboard(self):
        await self.bot.wait_until_ready()

    # --- 1. 個人等級查詢指令 ---
    @app_commands.command(name="rank", description="查看你的喝水等級與經驗值")
    async def rank(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        total_exp = database.get_user_total_exp(user_id)
        level, current_exp, req_exp = database.get_level_info(total_exp)
        diff_exp = req_exp - current_exp
        
        blocks = 10
        filled = int((current_exp / req_exp) * blocks)
        empty = blocks - filled
        progress_bar = ("■" * filled) + ("□" * empty)
        
        embed = discord.Embed(color=0x2b2d31)
        embed.set_author(name=f"{interaction.user.display_name} 等級資訊", icon_url=interaction.user.display_avatar.url)
        
        description = (
            f"📝 **喝水等級**\n"
            f"等級：**{level}**\n"
            f"經驗：**{current_exp} / {req_exp}** (還差 {diff_exp})\n"
            f"進度：`{progress_bar}`"
        )
        embed.description = description
        
        # 注意：你原本的程式碼中把按鈕面板註解掉了，我在此維持你的註解狀態
        # view = ResetLevelView(author_id=user_id)
        # await interaction.response.send_message(embed=embed, view=view, delete_after=10)
        await interaction.response.send_message(embed=embed, delete_after=10)

    # --- 2. 排行榜查詢指令 (包含分頁功能) ---
    @app_commands.command(name="leaderboard", description="查看所有參與喝水修煉的道友名單")
    @app_commands.describe(page="要查看的頁數 (預設為第 1 頁)")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        if page < 1:
            page = 1
            
        items_per_page = 10
        total_users = database.get_total_participants_count()
        
        if total_users == 0:
            await interaction.response.send_message("目前尚未有道友開始修煉喵。", ephemeral=True)
            return

        total_pages = (total_users + items_per_page - 1) // items_per_page
        
        if page > total_pages:
            page = total_pages

        offset = (page - 1) * items_per_page
        data = database.get_participants_paged(items_per_page, offset)

        embed = discord.Embed(title="📜 飲水修煉榜", color=0x7289da)
        
        leaderboard_text = ""
        for i, (u_id, total_exp) in enumerate(data, start=offset + 1):
            level, _, _ = database.get_level_info(total_exp)
            
            # 從常數檔取得身分組 ID 與純文字稱號
            role_id = ROLE_MAPPING.get(level)
            title_info = TITLE_DATA.get(level)
            fallback_title = title_info["title"] if title_info else "未知領域"
            
            # 如果有對應的 ID，就用 <@&ID> 來顯示帶顏色的身分組；否則顯示純文字
            display_title = f"<@&{role_id}>" if role_id else f"【{fallback_title}】"
            
            member = interaction.guild.get_member(int(u_id))
            name = member.display_name if member else f"隱世道友({u_id})"
            
            # 設定前三名的專屬獎牌符號
            if i == 1:
                rank_icon = "🥇"
            elif i == 2:
                rank_icon = "🥈"
            elif i == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"` {i} `"
            
            # 新排版：名次符號 -> 等級 -> 彩色稱號 -> 名字 -> 經驗值
            leaderboard_text += f"{rank_icon} **Lv.{level}** {display_title} **{name}** (經驗: {total_exp})\n"

        embed.description = leaderboard_text
        embed.set_footer(text=f"第 {page} 頁 / 共 {total_pages} 頁 (總計 {total_users} 名道友)")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))