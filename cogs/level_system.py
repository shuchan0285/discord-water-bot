import discord
from discord.ext import commands
from discord import app_commands
import database
from constants import TITLE_DATA, ROLE_MAPPING

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