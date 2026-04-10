# cogs/water_reminder.py
import discord
from discord.ext import tasks, commands
import datetime
import database
from constants import TITLE_DATA, ROLE_MAPPING

class WaterButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="喝了！", style=discord.ButtonStyle.success, emoji="🥤", custom_id="drink_water_btn")
    async def drink_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        user_id = interaction.user.id

        active_id = database.get_active_water_message()
        if str(message_id) != active_id:
            await interaction.response.send_message("⚠️ 這則是舊的通知，已經過期囉！請找最新的訊息打卡。", ephemeral=True)
            return

        # 🆕 接收包含 old_total 和 combo 的回傳值
        success, old_total, new_total, combo, bonus_exp = database.claim_exp(message_id, user_id)
        
        if not success:
            await interaction.response.send_message("❌ 你很皮喔，你已經打過卡了不是嘛！", ephemeral=True)
            return

        # 🆕 計算舊等級與新等級來判斷是否升級
        old_level, _, _ = database.get_level_info(old_total)
        new_level, _, _ = database.get_level_info(new_total)
        title_info = TITLE_DATA.get(new_level)
        title = title_info["title"] if title_info else "未知領域"

        # 組合基礎成功訊息
        msg = f"✅ {interaction.user.mention} 打卡成功！獲得 10 EXP"
        
        # 若有觸發獎勵，則顯示額外經驗
        if bonus_exp > 0:
            msg += f" 🎁 **(觸發 5 Combo 獎勵，額外 +{bonus_exp} EXP!)**"
            
        msg += f" (目前等級: **Lv.{new_level}**)"
        
        # 加入 Combo 特效
        if combo >= 2:
            msg += f" 🔥 **Combo x{combo}!**"

        # 判斷是否為第一次打卡或升級
        if old_total == 0:
            msg += f"\n🎉 **歡迎加入喝水行列！獲得稱號：【{title}】**"
            
            # 實作：發放等級 1 的身分組
            role_id = ROLE_MAPPING.get(new_level)
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    try:
                        await interaction.user.add_roles(role)
                    except discord.Forbidden:
                        print(f"⚠️ [警告] 權限不足，無法發放 {role.name} 身分組給 {interaction.user.display_name}")
                        
        elif new_level > old_level:
            msg += f"\n🏆 **恭喜升級啦！獲得新稱號：【{title}】**"
            
            # 實作：移除舊身分組，發放新身分組
            old_role_id = ROLE_MAPPING.get(old_level)
            new_role_id = ROLE_MAPPING.get(new_level)
            
            roles_to_remove = []
            roles_to_add = []
            
            # 取得舊身分組物件
            if old_role_id:
                old_role = interaction.guild.get_role(old_role_id)
                if old_role:
                    roles_to_remove.append(old_role)
                    
            # 取得新身分組物件
            if new_role_id:
                new_role = interaction.guild.get_role(new_role_id)
                if new_role:
                    roles_to_add.append(new_role)
            
            # 執行替換
            try:
                if roles_to_remove:
                    await interaction.user.remove_roles(*roles_to_remove)
                if roles_to_add:
                    await interaction.user.add_roles(*roles_to_add)
            except discord.Forbidden:
                print(f"⚠️ [警告] 權限不足，無法為 {interaction.user.display_name} 切換身分組")
        
        await interaction.response.send_message(msg)

class WaterReminder(commands.Cog):
    # 下方保持不變... (原封不動保留你的 __init__, water_task, test_water 等)
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 1491748943690993875 # ⚠️ 請填入你的頻道 ID
        self.water_task.start()

    def cog_unload(self):
        self.water_task.cancel()

    tz = datetime.timezone(datetime.timedelta(hours=8))
    trigger_times = []
    for h in range(10, 24):
        trigger_times.append(datetime.time(hour=h, minute=0, tzinfo=tz))
        trigger_times.append(datetime.time(hour=h, minute=30, tzinfo=tz))

    @tasks.loop(time=trigger_times)
    async def water_task(self):
        channel = self.bot.get_channel(self.target_channel_id)
        if channel:
            message = await channel.send("🥤 **喝水啦！** 該喝水啦！身體要渴死啦！", view=WaterButtonView())
            database.set_active_water_message(message.id)
            print(f"[{datetime.datetime.now().strftime('%H:%M')}] 已發送最新通知：{message.id}")

    @commands.command(name="test_water")
    async def test_water(self, ctx):
        message = await ctx.send("[補]🥤 **喝水啦！** 該喝水啦！身體要渴死啦！", view=WaterButtonView())
        database.set_active_water_message(message.id)
        await ctx.message.delete()

    @water_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(WaterReminder(bot))
    bot.add_view(WaterButtonView())