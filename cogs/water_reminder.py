# cogs/water_reminder.py
import discord
from discord.ext import tasks, commands
import datetime
import database
from constants import TITLE_DATA, ROLE_MAPPING
import event_manager
import json
import random
import os

sys_event_manager = event_manager.EventManager()

class SleepButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="我要睡覺了", style=discord.ButtonStyle.blurple, emoji="🛏️", custom_id="sleep_btn")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        data = database.get_user_today_summary(user_id)
        
        if not data:
            await interaction.response.send_message("道友今日尚未引水入體，快去喝杯水再來歇息吧！", ephemeral=True)
            return

        total_exp, combo, daily_exp, _ = data
        
        # 產生睡前總結報告
        embed = discord.Embed(title="🌙 閉關就寢報告", color=0x2b2d31)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(
            name="今日修行總結", 
            value=f"今日修為增長：**{daily_exp}** EXP\n當前心法連段：**{combo}** Combo\n累積總合修為：**{total_exp}**", 
            inline=False
        )
        embed.set_footer(text="仙人祝你一夜好眠，明日莫忘繼續補水。")

        # 讓這則總結只有自己看得到
        await interaction.response.send_message(embed=embed, ephemeral=True)

class WaterButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="喝了！", style=discord.ButtonStyle.success, emoji="🥤", custom_id="drink_water_btn")
    async def drink_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        user_id = interaction.user.id

        active_id = database.get_active_water_message()
        if str(message_id) != active_id:
            await interaction.response.send_message("🙄這我都通知多久了你才來點...", ephemeral=True)
            return
        
        # 1. 先從資料庫取得今日運勢 Buff (若為今日第一次喝水，此處會回傳空字串)
        daily_fortune_buff = database.get_user_daily_fortune(user_id)

        # 2. 將 Buff 傳入機緣系統影響抽獎機率
        drawn_event = sys_event_manager.get_random_event(daily_fortune_buff)
        event_exp = drawn_event["exp"] if drawn_event else 0
        event_text = drawn_event["text"] if drawn_event else ""

        # 3. 結算經驗值
        success, old_total, new_total, combo, bonus_exp, is_first_of_day = database.claim_exp(
            message_id, user_id, event_exp, event_text)
        
        if not success:
            await interaction.response.send_message("😒你很皮喔，你已經打過卡了不是嘛！", ephemeral=True)
            return

        # 🆕 計算舊等級與新等級來判斷是否升級
        old_level, _, _ = database.get_level_info(old_total)
        new_level, _, _ = database.get_level_info(new_total)
        title_info = TITLE_DATA.get(new_level)
        title = title_info["title"] if title_info else "未知領域"

        # ==========================================
        # 重新設計的 UI 文字排版 (使用陣列收集每一行)
        # ==========================================
        lines = []
        lines.append(f"✅ **{interaction.user.mention} 打卡成功！**")
        
        # 1. 數值結算區塊 (使用 > 產生縮排視覺效果)
        lines.append("> 💧 基礎修為：`+10 EXP`")
        
        if drawn_event:
            lines.append(f"> {drawn_event['emoji']} **突發機緣**：{drawn_event['exp']:+d} EXP ({drawn_event['text']})")
            
        if bonus_exp > 0:
            lines.append(f"> 🎁 **連擊獎勵**：Combo x{combo}! `(+{bonus_exp} EXP)`")
        elif combo >= 2:
            lines.append(f"> 🔥 **連續打卡**：Combo x{combo}!")

        lines.append(f"> 📊 **當前進度**：**Lv.{new_level}** (總修為: {new_total})")

        # 2. 升級與稱號提示 (空一行後獨立顯示，給予視覺強調)
        if old_total == 0:
            lines.append(f"\n🎉 **歡迎加入修煉！獲得稱號：【{title}】**")
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
            lines.append(f"\n🏆 **恭喜突破！獲得新稱號：【{title}】**")
            # 實作：移除舊身分組，發放新身分組
            old_role_id = ROLE_MAPPING.get(old_level)
            new_role_id = ROLE_MAPPING.get(new_level)
            
            roles_to_remove = []
            roles_to_add = []
            
            if old_role_id:
                old_role = interaction.guild.get_role(old_role_id)
                if old_role: roles_to_remove.append(old_role)
            if new_role_id:
                new_role = interaction.guild.get_role(new_role_id)
                if new_role: roles_to_add.append(new_role)
            
            try:
                if roles_to_remove: await interaction.user.remove_roles(*roles_to_remove)
                if roles_to_add: await interaction.user.add_roles(*roles_to_add)
            except discord.Forbidden:
                print(f"⚠️ [警告] 權限不足，無法為 {interaction.user.display_name} 切換身分組")

        # 4. 首日抽籤與綁架子邏輯
        fortune_embed = None
        fortune_type = ""
        
        if is_first_of_day:
            fortune_cog = interaction.client.get_cog("Fortune")
            if fortune_cog:
                # 接收修改後的 Tuple 回傳值
                result = fortune_cog.get_random_fortune_embed()
                if result[0]:
                    fortune_embed, fortune_type = result
                    lines.append("\n🔮 *仙人看你今日初次修煉，特賜運勢籤一支：*")
                    # 將抽到的運勢寫入資料庫
                    database.set_user_daily_fortune(user_id, fortune_type)

        final_msg = "\n".join(lines)
        
        # 5. 如果抽到凶，附上化解按鈕 UI；否則不附帶任何 View
        view_to_send = TieRackView(user_id) if fortune_type == "凶" else discord.utils.MISSING
        
        await interaction.response.send_message(
            content=final_msg, 
            embed=fortune_embed,
            view=view_to_send,
            delete_after=3600
        )

class TieRackView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=600)
        self.author_id = author_id

    @discord.ui.button(label="將凶籤綁在神木架上", style=discord.ButtonStyle.secondary, emoji="🎐")
    async def tie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("這是別人的厄運，當心引火上身！", ephemeral=True)
            return

        # 更新資料庫，將運勢狀態改為 "已化解"
        database.set_user_daily_fortune(self.author_id, "已化解")

        # 禁用按鈕並變更外觀
        button.disabled = True
        button.label = "厄運已隨風消散"
        button.style = discord.ButtonStyle.success

        await interaction.response.edit_message(view=self)

        file = discord.File("shrine.gif", filename="shrine.gif")
        success_embed = discord.Embed(
            description="💨 一陣微風吹過，你將凶籤綁在神木架上，今日的厄運似乎消散了...",
            color=0x2ECC71
        )
    
        success_embed.set_image(url="attachment://shrine.gif")
        await interaction.followup.send(embed=success_embed, file=file, ephemeral=True)

class WaterReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        default_id = os.getenv("DEFAULT_CHANNEL_ID")
        channel_id_str = database.get_setting("target_channel_id", default=default_id)
        self.target_channel_id = int(channel_id_str) if channel_id_str else 0
        self.messages_data = []
        self.load_messages()
        self.water_task.start()
        self.consecutive_skips = 0

    def cog_unload(self):
        self.water_task.cancel()

    def load_messages(self):
        file_path = "water_messages.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 確保讀取到的是列表，否則給予空列表
                    self.messages_data = data.get("messages", [])
                print(f"✅ 成功載入 {len(self.messages_data)} 筆喝水提醒文字。")
            else:
                print(f"❌ 找不到 {file_path} 檔案，將使用預設提醒文字。")
        except json.JSONDecodeError as e:
            print(f"❌ {file_path} 格式錯誤: {e}，將使用預設提醒文字。")
        except Exception as e:
            print(f"❌ 讀取 {file_path} 時發生未知錯誤: {e}")

    def get_random_message(self) -> str:
        # 實作回退機制 (Fallback)：如果 JSON 檔案不存在或為空，回傳預設字串
        if not self.messages_data:
            return "🥤 **喝水啦！** 該喝水啦！身體要渴死啦！"
        return random.choice(self.messages_data)

    # 設定觸發時間（每天 10:00 - 隔天02:00，每半小時一次）
    tz = datetime.timezone(datetime.timedelta(hours=8))
    trigger_times = []
    for h in range(10, 29):
        actual_h = h % 24
        trigger_times.append(datetime.time(hour=actual_h, minute=0, tzinfo=tz))
        trigger_times.append(datetime.time(hour=actual_h, minute=30, tzinfo=tz))
    trigger_times.pop()

    @tasks.loop(time=trigger_times)
    async def water_task(self):
        current_id = database.get_setting("target_channel_id", default=os.getenv("DEFAULT_CHANNEL_ID"))
        self.target_channel_id = int(current_id) if current_id else self.target_channel_id
        channel = self.bot.get_channel(self.target_channel_id)

        now = datetime.datetime.now()

        # 1. 每天早上 10 點，強制解除睡眠模式並重置未讀計數
        if now.hour == 10 and now.minute == 0:
            database.set_setting("is_sleeping", "false")
            database.reset_missed_rounds()

        # 2. 檢查是否處於深夜提早結束的「睡眠模式」
        if database.get_setting("is_sleeping", "false") == "true":
            return

        # 3. 檢查上一則訊息是否有人點擊
        if not database.check_last_message_claimed():
            database.increment_missed_rounds()
        else:
            database.reset_missed_rounds()

        missed = int(database.get_setting("consecutive_missed", 0))

        # 4. 判定是否觸發提早結束 (嚴格限制在凌晨 0 點到 4 點之間)
        should_stop = False
        if 0 <= now.hour <= 4:
            if now.hour >= 2 and missed >= 3:
                should_stop = True
            elif missed >= 5:
                should_stop = True

        if should_stop:
            # 觸發結算並進入睡眠模式，取代原本的 cancel()
            level_cog = self.bot.get_cog("LevelSystem")
            if level_cog:
                await level_cog.daily_leaderboard_task() # 執行每日總結

            database.reset_missed_rounds()
            database.set_setting("is_sleeping", "true") # 標記為睡眠狀態
            print(f"[{now.strftime('%H:%M')}] 深夜無人回應，提前結束今日修煉，進入睡眠模式。")
            return
        
        # 5. 發送提醒訊息
        if channel:
            msg_content = self.get_random_message()
            view = WaterButtonView()
            current_hour = now.hour
            if 0 <= current_hour <= 3:
                # 動態加入睡覺按鈕
                view.add_item(SleepButton())

            message = await channel.send(
                msg_content, 
                view=view,
                delete_after=3600
            )
            database.set_active_water_message(message.id)
            print(f"[{now.strftime('%H:%M')}] 已發送最新通知：{message.id}")

async def setup(bot):
    await bot.add_cog(WaterReminder(bot))
    bot.add_view(WaterButtonView())