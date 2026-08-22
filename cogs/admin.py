# cogs/admin.py
import discord
from discord.ext import commands
from discord import app_commands
import database
import os
# 引用常數檔案中的 TITLE_DATA 與 ROLE_MAPPING
from constants import ROLE_MAPPING, TITLE_DATA

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    admin_group = app_commands.Group(
        name="admin",
        description="管理員專用的喝水系統控制指令",
        default_permissions=discord.Permissions(administrator=True)
    )

    # ==========================================
    # 用戶數據與資料庫管理
    # ==========================================

    # 1. 設定目標頻道 (喝水提醒 / 排行榜 / 新聞早報共用)
    @admin_group.command(name="set_channel", description="設定喝水提醒、排行榜、新聞早報要發送的目標頻道")
    @app_commands.describe(channel="目標頻道 (若不填則使用當前頻道)")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel

        # 將 ID 存入資料庫
        database.set_setting("target_channel_id", str(target_channel.id))

        # 同步更新目前已載入模組中的變數 (避免等待下次重啟)
        cogs_to_update = ["LevelSystem", "WaterReminder", "DailyNews"]
        for cog_name in cogs_to_update:
            cog = self.bot.get_cog(cog_name)
            if cog:
                cog.target_channel_id = target_channel.id

        await interaction.response.send_message(f"已將目標頻道切換至：{target_channel.mention}", ephemeral=True)

    # 2. 查水表 (查看使用者後台數據)
    @admin_group.command(name="check", description="查看指定使用者的後台詳細數據")
    async def check(self, interaction: discord.Interaction, member: discord.Member):
        data = database.get_user_full_data(member.id)
        if not data:
            await interaction.response.send_message(f"找不到 {member.display_name} 的資料。", ephemeral=True)
            return

        total_exp, combo, last_round = data
        level, current_exp, req_exp = database.get_level_info(total_exp)

        msg = (
            f"**{member.display_name} 後台數據**\n"
            f"等級：Lv.{level}\n"
            f"總經驗值：{total_exp}\n"
            f"當前級別進度：{current_exp} / {req_exp}\n"
            f"連續打卡 (Combo)：{combo}\n"
            f"最後打卡系統回合：{last_round}"
        )
        await interaction.response.send_message(msg, ephemeral=True)

    # 2. 備份資料庫
    @admin_group.command(name="backup_db", description="取得當前資料庫檔案備份")
    async def backup_db(self, interaction: discord.Interaction):
        db_path = database.DB_NAME # "water_exp.db"
        if os.path.exists(db_path):
            file = discord.File(db_path, filename=f"backup_{database.DB_NAME}")
            await interaction.response.send_message("這是目前的資料庫備份檔案：", file=file, ephemeral=True)
        else:
            await interaction.response.send_message("找不到資料庫檔案。", ephemeral=True)

    # 3. 徹底刪除使用者
    @admin_group.command(name="remove_user", description="徹底刪除使用者的所有資料 (不可復原)")
    async def remove_user(self, interaction: discord.Interaction, member: discord.Member):
        database.remove_user_data(member.id)
        await interaction.response.send_message(f"已徹底刪除 {member.display_name} 的所有經驗值與打卡紀錄。", ephemeral=True)

    # 4. 調整經驗值 (增加或扣除)
    @admin_group.command(name="add_exp", description="給予或扣除使用者的經驗值")
    @app_commands.describe(amount="要增加的經驗值 (輸入負數則為扣除)")
    async def add_exp(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        old_exp, new_exp = database.modify_user_exp(member.id, amount, mode="add")
        await interaction.response.send_message(f"已將 {member.display_name} 的經驗值調整：{old_exp} -> **{new_exp}** (變動: {amount:+d})", ephemeral=True)

    # 5. 強制設定經驗值
    @admin_group.command(name="set_exp", description="強制設定使用者的經驗值")
    @app_commands.describe(amount="要設定的最終經驗值數值")
    async def set_exp(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount < 0:
            amount = 0
        old_exp, new_exp = database.modify_user_exp(member.id, amount, mode="set")
        await interaction.response.send_message(f"已強制將 {member.display_name} 的經驗值設定為：**{new_exp}** (原為: {old_exp})", ephemeral=True)

    # 6. 重置使用者經驗與連擊
    @admin_group.command(name="reset", description="將使用者的經驗值、Combo 與回合數歸零 (不刪除打卡紀錄)")
    async def reset(self, interaction: discord.Interaction, member: discord.Member):
        database.reset_user_exp(member.id)
        await interaction.response.send_message(f"已將 {member.display_name} 的修為、連擊進度全部歸零。", ephemeral=True)


    # ==========================================
    # 系統排程與訊息控制
    # ==========================================

    # 1. 強制觸發打卡通知
    @admin_group.command(name="trigger_water", description="立即發送一則喝水打卡通知")
    async def trigger_water(self, interaction: discord.Interaction):
        water_cog = self.bot.get_cog("WaterReminder")
        if water_cog:
            await water_cog.water_task()
            await interaction.response.send_message("已成功手動觸發喝水通知。", ephemeral=True)
        else:
            await interaction.response.send_message("找不到 WaterReminder 模組。", ephemeral=True)

    # 2. 立即觸發每日新聞早報
    @admin_group.command(name="trigger_news", description="立即執行一次每日新聞早報")
    async def trigger_news(self, interaction: discord.Interaction):
        news_cog = self.bot.get_cog("DailyNews")
        if not news_cog:
            await interaction.response.send_message("找不到 DailyNews 模組。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await news_cog.news_task()
        await interaction.followup.send("已手動觸發一次新聞早報。", ephemeral=True)

    # 3. 切換排程開關
    @admin_group.command(name="toggle_water", description="開啟或關閉自動喝水提醒排程")
    @app_commands.choices(action=[
        app_commands.Choice(name="啟動排程", value="start"),
        app_commands.Choice(name="停止排程", value="stop")
    ])
    async def toggle_water(self, interaction: discord.Interaction, action: str):
        water_cog = self.bot.get_cog("WaterReminder")
        if not water_cog:
            await interaction.response.send_message("找不到 WaterReminder 模組。", ephemeral=True)
            return

        if action == "start":
            if not water_cog.water_task.is_running():
                water_cog.water_task.start()
                await interaction.response.send_message("喝水排程已啟動。", ephemeral=True)
            else:
                await interaction.response.send_message("排程本來就在運行中。", ephemeral=True)
        else:
            water_cog.water_task.cancel()
            await interaction.response.send_message("喝水排程已停止運作。", ephemeral=True)

    # 4. 批次清理頻道訊息 (Purge)
    @admin_group.command(name="clear", description="快速清理頻道內的指定數量訊息")
    @app_commands.describe(amount="要往上刪除幾則訊息？ (預設 5，最多建議 100)")
    async def clear_messages(self, interaction: discord.Interaction, amount: int = 5):
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"清理完畢！已成功刪除 {len(deleted)} 則訊息。", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("機器人權限不足，無法刪除訊息。", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"發生未預期的 API 錯誤：{e}", ephemeral=True)


    # ==========================================
    # 伺服器身分組建置與管理
    # ==========================================

    # 1. 自動批次建立稱號身分組並產生 Mapping
    @admin_group.command(name="create_roles", description="自動批次建立喝水修煉的 30 個稱號身分組並產生 Mapping")
    async def create_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("正在為伺服器批次建立身分組...", ephemeral=True)

        guild = interaction.guild
        created_count = 0
        mapping_lines = ["ROLE_MAPPING = {"]

        # 替換為直接讀取 constants 中的 TITLE_DATA
        for level, data in TITLE_DATA.items():
            role_name = data["title"]
            hex_color = data["color"]
            color_int = int(hex_color.lstrip('#'), 16)
            discord_color = discord.Color(color_int)

            try:
                new_role = await guild.create_role(
                    name=role_name,
                    color=discord_color,
                    hoist=False,
                    mentionable=False,
                    reason=f"管理員批次建立喝水稱號"
                )
                created_count += 1
                mapping_lines.append(f"    {level}: {new_role.id},  # {role_name}")

            except discord.Forbidden:
                await interaction.followup.send("錯誤：權限不足，無法建立身分組。", ephemeral=True)
                return
            except Exception as e:
                print(f"建立身分組 {role_name} 失敗: {e}")

        mapping_lines.append("}")
        final_mapping_string = "\n".join(mapping_lines)

        import io
        file_obj = io.BytesIO(final_mapping_string.encode('utf-8'))
        file = discord.File(file_obj, filename="role_mapping.py")

        await interaction.followup.send(f"成功！建立了 {created_count} 個身分組。\n這裡為你自動產生了 `ROLE_MAPPING` 程式碼，請下載這個檔案並將內容更新回你的 `constants.py`：", file=file, ephemeral=True)

    # 2. 產生現有身分組的 Mapping 程式碼
    @admin_group.command(name="generate_mapping", description="從伺服器現有的身分組中，搜尋並產生 ROLE_MAPPING 程式碼")
    async def generate_mapping(self, interaction: discord.Interaction):
        guild = interaction.guild
        mapping_lines = ["ROLE_MAPPING = {"]
        found_count = 0
        missing_roles = []

        # 替換為直接讀取 constants 中的 TITLE_DATA
        for level, data in TITLE_DATA.items():
            expected_name = data["title"]  # 修正迴圈變數的取值錯誤
            role = discord.utils.get(guild.roles, name=expected_name)
            if role:
                mapping_lines.append(f"    {level}: {role.id},  # {expected_name}")
                found_count += 1
            else:
                mapping_lines.append(f"    {level}: None,  # 找不到名為 '{expected_name}' 的身分組")
                missing_roles.append(expected_name)

        mapping_lines.append("}")
        final_mapping_string = "\n".join(mapping_lines)

        import io
        file_obj = io.BytesIO(final_mapping_string.encode('utf-8'))
        file = discord.File(file_obj, filename="role_mapping.py")

        msg = f"掃描完成。找到了 {found_count} 個對應的身分組。"
        if missing_roles:
            msg += f"\n有 {len(missing_roles)} 個稱號找不到對應的身分組，已在檔案中標記為 None。"

        await interaction.response.send_message(msg, file=file, ephemeral=True)


    # ==========================================
    # 開發測試與除錯工具
    # ==========================================

    # 1. 測試仙人歡迎訊息
    @admin_group.command(name="test_welcome", description="手動測試機器人加入伺服器時的仙人歡迎訊息")
    async def test_welcome(self, interaction: discord.Interaction):
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
        await interaction.response.send_message("正在發送仙人歡迎訊息...", ephemeral=True)
        await interaction.channel.send(welcome_msg)

    # 2. 重設今日打卡狀態
    @admin_group.command(name="reset_daily", description="消除使用者的今日打卡紀錄，使其能再次觸發抽籤")
    async def reset_daily(self, interaction: discord.Interaction, member: discord.Member):
        database.reset_user_daily_status(member.id)
        await interaction.response.send_message(f"已清空 {member.display_name} 的今日打卡狀態！", ephemeral=True)

    # 3. 強制校準等級與身分組
    @admin_group.command(name="sync_level", description="根據當前實際經驗值，重新派發正確的等級稱號")
    async def sync_level(self, interaction: discord.Interaction, member: discord.Member):
        data = database.get_user_full_data(member.id)
        if not data:
            await interaction.response.send_message("找不到該道友的資料。", ephemeral=True)
            return

        total_exp = data[0]
        correct_level, _, _ = database.get_level_info(total_exp)
        correct_role_id = ROLE_MAPPING.get(correct_level)

        roles_to_remove = []
        for role_id in ROLE_MAPPING.values():
            if not role_id: continue
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)

        await interaction.response.defer(ephemeral=True)

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            if correct_role_id:
                correct_role = interaction.guild.get_role(correct_role_id)
                if correct_role:
                    await member.add_roles(correct_role)

            await interaction.followup.send(f"已將 {member.display_name} 的境界強制校準為 **Lv.{correct_level}**。多餘的稱號已全部剝奪。", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("錯誤：機器人權限不足，無法變更身分組。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))