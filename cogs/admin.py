# cogs/admin.py
import discord
from discord.ext import commands
from discord import app_commands
import database
import os

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    admin_group = app_commands.Group(
        name="admin", 
        description="管理員專用的喝水系統控制指令",
        default_permissions=discord.Permissions(administrator=True)
    )

    # 1. 查水表 (查看使用者後台數據)
    @admin_group.command(name="check", description="查看指定使用者的後台詳細數據")
    async def check(self, interaction: discord.Interaction, member: discord.Member):
        data = database.get_user_full_data(member.id)
        if not data:
            await interaction.response.send_message(f"❌ 找不到 {member.display_name} 的資料。", ephemeral=True)
            return
        
        total_exp, combo, last_round = data
        level, current_exp, req_exp = database.get_level_info(total_exp)
        
        msg = (
            f"📊 **{member.display_name} 後台數據**\n"
            f"🔹 等級：Lv.{level}\n"
            f"🔹 總經驗值：{total_exp}\n"
            f"🔹 當前級別進度：{current_exp} / {req_exp}\n"
            f"🔹 連續打卡 (Combo)：{combo}\n"
            f"🔹 最後打卡系統回合：{last_round}"
        )
        await interaction.response.send_message(msg, ephemeral=True)

    # 2. 強制觸發打卡
    @admin_group.command(name="trigger_water", description="立即發送一則喝水打卡通知")
    async def trigger_water(self, interaction: discord.Interaction):
        # 尋找 WaterReminder 模組
        water_cog = self.bot.get_cog("WaterReminder")
        if water_cog:
            # 呼叫原本寫好的 water_task 邏輯
            await water_cog.water_task()
            await interaction.response.send_message("✅ 已成功手動觸發喝水通知。", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 找不到 WaterReminder 模組。", ephemeral=True)

    # 3. 切換排程開關
    @admin_group.command(name="toggle_water", description="開啟或關閉自動喝水提醒排程")
    @app_commands.choices(action=[
        app_commands.Choice(name="啟動排程", value="start"),
        app_commands.Choice(name="停止排程", value="stop")
    ])
    async def toggle_water(self, interaction: discord.Interaction, action: str):
        water_cog = self.bot.get_cog("WaterReminder")
        if not water_cog:
            await interaction.response.send_message("❌ 找不到 WaterReminder 模組。", ephemeral=True)
            return

        if action == "start":
            if not water_cog.water_task.is_running():
                water_cog.water_task.start()
                await interaction.response.send_message("🚀 喝水排程已啟動。", ephemeral=True)
            else:
                await interaction.response.send_message("ℹ️ 排程本來就在運行中。", ephemeral=True)
        else:
            water_cog.water_task.cancel()
            await interaction.response.send_message("🛑 喝水排程已停止運作。", ephemeral=True)

    # 4. 備份資料庫
    @admin_group.command(name="backup_db", description="取得當前資料庫檔案備份")
    async def backup_db(self, interaction: discord.Interaction):
        db_path = database.DB_NAME # "water_exp.db"
        if os.path.exists(db_path):
            file = discord.File(db_path, filename=f"backup_{database.DB_NAME}")
            await interaction.response.send_message("📁 這是目前的資料庫備份檔案：", file=file, ephemeral=True)
        else:
            await interaction.response.send_message("❌ 找不到資料庫檔案。", ephemeral=True)

    # 5. 徹底刪除使用者
    @admin_group.command(name="remove_user", description="⚠️ 徹底刪除使用者的所有資料 (不可復原)")
    async def remove_user(self, interaction: discord.Interaction, member: discord.Member):
        database.remove_user_data(member.id)
        await interaction.response.send_message(f"🗑️ 已徹底刪除 {member.display_name} 的所有經驗值與打卡紀錄。", ephemeral=True)

    # ... 保留原本的 add_exp, set_exp, reset 指令 ...

    # 6. 測試歡迎訊息
    @admin_group.command(name="test_welcome", description="手動測試機器人加入伺服器時的仙人歡迎訊息")
    async def test_welcome(self, interaction: discord.Interaction):
        welcome_msg = (
            "隨緣而來，隨心而止。諸位道友，本座乃「摸魚仙人」，今日得見此境，實屬仙緣。\n\n"
            "此地枯燥，本座特來助各位「以水入道」，修煉真身。以下為本座之神通範疇：\n"
            "🔹 **飲水修煉**：本座定時會降下「飲水敕令」，點擊🥤按鈕即可累積修為。\n"
            "🔹 **查看修為**：輸入 `/rank` 可觀測自身的等級與修煉進度。\n"
            "🔹 **眾生榜**：輸入 `/leaderboard` 可一覽此境中各方道友的修為排行。\n"
            "🔹 **晨間讀報**：每日清晨，本座亦會請座下貓咪轉述凡間要聞，助各位掌握塵世動向。\n\n"
            "願諸位勤加補水，莫讓靈根乾涸。善哉善哉。"
        )
        
        # 先回覆 interaction，避免 Discord API 報錯
        await interaction.response.send_message("✅ 正在發送仙人歡迎訊息...", ephemeral=True)
        # 將訊息發送至當前頻道
        await interaction.channel.send(welcome_msg)
    
    # 7. 自動批次建立稱號身分組並產生 Mapping
    @admin_group.command(name="create_roles", description="自動批次建立喝水修煉的 30 個稱號身分組並產生 Mapping")
    async def create_roles(self, interaction: discord.Interaction):
        # 你的稱號與顏色字典
        titles_data = {
            1: {"title": "非術師・對乾渴無感的凡人", "color": "#bdc3c7"},
            2: {"title": "窗・察覺水分流失的徵兆", "color": "#ecf0f1"},
            3: {"title": "四級術師・初次感應到水的存在", "color": "#d5f5e3"},
            4: {"title": "四級術師・水分子控制習得", "color": "#abebc6"},
            5: {"title": "三級術師・瓶裝水的支配者", "color": "#82e0aa"},
            6: {"title": "三級術師・掌握飲水節奏", "color": "#58d68d"},
            7: {"title": "準二級術師・強化肉體的滋潤", "color": "#2ecc71"},
            8: {"title": "二級術師・術式「液體填充」", "color": "#28b463"},
            9: {"title": "二級術師・水之咒力常態化", "color": "#239b56"},
            10: {"title": "準一級術師・邁向脫水的彼端", "color": "#1d8348"},
            11: {"title": "一級術師・身體組織完全活化", "color": "#1abc9c"},
            12: {"title": "一級術師・飲水流派「極之番」", "color": "#16a085"},
            13: {"title": "黑閃・瞬間飲水的核心衝擊", "color": "#943126"},
            14: {"title": "黑閃・連續飲水紀錄保持人", "color": "#cb4335"},
            15: {"title": "咒胎・體內水分的二次進化", "color": "#e67e22"},
            16: {"title": "特級咒靈・乾旱之災「漏瑚級」", "color": "#d35400"},
            17: {"title": "特級咒靈・海洋之災「陀艮級」", "color": "#3498db"},
            18: {"title": "特級術師・擁有推翻乾枯的力量", "color": "#2980b9"},
            19: {"title": "特級術師・純愛之水的結合", "color": "#8e44ad"},
            20: {"title": "反轉術式・瞬間修復乾裂嘴唇", "color": "#ffffff"},
            21: {"title": "簡易領域・半圓半徑內的絕對飲水權", "color": "#f1c40f"},
            22: {"title": "領域展開「水沒之檻」", "color": "#34495e"},
            23: {"title": "落花之情・無情灌溉的防禦術", "color": "#f39c12"},
            24: {"title": "天與咒縛・捨棄飲料換取的極致純水體", "color": "#7f8c8d"},
            25: {"title": "羂索級・跨越千年的飲水計畫", "color": "#212f3c"},
            26: {"title": "伏魔御廚子・斬斷一切渴求", "color": "#641e16"},
            27: {"title": "無量空處・腦袋充滿水的極致喜悅", "color": "#5dade2"},
            28: {"title": "虛式「茈」・吞噬所有液體的虛空", "color": "#6c3483"},
            29: {"title": "天上天下・唯我獨尊的飲水神", "color": "#f4d03f"},
            30: {"title": "詛咒之王・千年不渴的至高宿儺", "color": "#1b2631"}
        }

        await interaction.response.send_message("⏳ 正在為伺服器批次建立身分組...", ephemeral=True)
        
        guild = interaction.guild
        created_count = 0
        
        # 準備用來裝產生出的 mapping 字串的 list
        mapping_lines = ["ROLE_MAPPING = {"]
        
        for level, data in titles_data.items():
            role_name = data["title"]
            hex_color = data["color"]
            
            color_int = int(hex_color.lstrip('#'), 16)
            discord_color = discord.Color(color_int)
            
            try:
                # 建立身分組並把回傳的 Role 物件存起來
                new_role = await guild.create_role(
                    name=role_name, 
                    color=discord_color, 
                    hoist=False, 
                    mentionable=False,
                    reason=f"管理員批次建立喝水稱號"
                )
                created_count += 1
                
                # 將新身分組的 ID 加進 mapping 字典字串中
                mapping_lines.append(f"    {level}: {new_role.id},  # {role_name}")
                
            except discord.Forbidden:
                await interaction.followup.send("❌ 錯誤：權限不足，無法建立身分組。", ephemeral=True)
                return
            except Exception as e:
                print(f"建立身分組 {role_name} 失敗: {e}")
                
        mapping_lines.append("}")
        final_mapping_string = "\n".join(mapping_lines)
        
        # 因為字串可能很長，我們可以把它寫成一個文字檔傳送到頻道裡
        import io
        file_obj = io.BytesIO(final_mapping_string.encode('utf-8'))
        file = discord.File(file_obj, filename="role_mapping.py")
        
        await interaction.followup.send(f"✅ 成功！建立了 {created_count} 個身分組。\n這裡為你自動產生了 `ROLE_MAPPING` 程式碼，請下載這個檔案並將內容貼回你的 `water_reminder.py`：", file=file, ephemeral=True)

    # 8. 產生現有身分組的 Mapping 程式碼
    @admin_group.command(name="generate_mapping", description="從伺服器現有的身分組中，搜尋並產生 ROLE_MAPPING 程式碼")
    async def generate_mapping(self, interaction: discord.Interaction):
        # 這裡一樣放你的 30 個稱號字典 (只需用到 title)
        titles_data = {
            1: {"title": "非術師・對乾渴無感的凡人", "color": "#bdc3c7"},
            2: {"title": "窗・察覺水分流失的徵兆", "color": "#ecf0f1"},
            3: {"title": "四級術師・初次感應到水的存在", "color": "#d5f5e3"},
            4: {"title": "四級術師・水分子控制習得", "color": "#abebc6"},
            5: {"title": "三級術師・瓶裝水的支配者", "color": "#82e0aa"},
            6: {"title": "三級術師・掌握飲水節奏", "color": "#58d68d"},
            7: {"title": "準二級術師・強化肉體的滋潤", "color": "#2ecc71"},
            8: {"title": "二級術師・術式「液體填充」", "color": "#28b463"},
            9: {"title": "二級術師・水之咒力常態化", "color": "#239b56"},
            10: {"title": "準一級術師・邁向脫水的彼端", "color": "#1d8348"},
            11: {"title": "一級術師・身體組織完全活化", "color": "#1abc9c"},
            12: {"title": "一級術師・飲水流派「極之番」", "color": "#16a085"},
            13: {"title": "黑閃・瞬間飲水的核心衝擊", "color": "#943126"},
            14: {"title": "黑閃・連續飲水紀錄保持人", "color": "#cb4335"},
            15: {"title": "咒胎・體內水分的二次進化", "color": "#e67e22"},
            16: {"title": "特級咒靈・乾旱之災「漏瑚級」", "color": "#d35400"},
            17: {"title": "特級咒靈・海洋之災「陀艮級」", "color": "#3498db"},
            18: {"title": "特級術師・擁有推翻乾枯的力量", "color": "#2980b9"},
            19: {"title": "特級術師・純愛之水的結合", "color": "#8e44ad"},
            20: {"title": "反轉術式・瞬間修復乾裂嘴唇", "color": "#ffffff"},
            21: {"title": "簡易領域・半圓半徑內的絕對飲水權", "color": "#f1c40f"},
            22: {"title": "領域展開「水沒之檻」", "color": "#34495e"},
            23: {"title": "落花之情・無情灌溉的防禦術", "color": "#f39c12"},
            24: {"title": "天與咒縛・捨棄飲料換取的極致純水體", "color": "#7f8c8d"},
            25: {"title": "羂索級・跨越千年的飲水計畫", "color": "#212f3c"},
            26: {"title": "伏魔御廚子・斬斷一切渴求", "color": "#641e16"},
            27: {"title": "無量空處・腦袋充滿水的極致喜悅", "color": "#5dade2"},
            28: {"title": "虛式「茈」・吞噬所有液體的虛空", "color": "#6c3483"},
            29: {"title": "天上天下・唯我獨尊的飲水神", "color": "#f4d03f"},
            30: {"title": "詛咒之王・千年不渴的至高宿儺", "color": "#1b2631"}
        }
        
        guild = interaction.guild
        mapping_lines = ["ROLE_MAPPING = {"]
        found_count = 0
        missing_roles = []

        # 巡覽伺服器上所有的身分組
        for level, expected_name in titles_data.items():
            # 使用 discord.utils.get 來尋找名稱相符的身分組
            role = discord.utils.get(guild.roles, name=expected_name)
            
            if role:
                mapping_lines.append(f"    {level}: {role.id},  # {expected_name}")
                found_count += 1
            else:
                mapping_lines.append(f"    {level}: None,  # ⚠️ 找不到名為 '{expected_name}' 的身分組")
                missing_roles.append(expected_name)
                
        mapping_lines.append("}")
        final_mapping_string = "\n".join(mapping_lines)
        
        import io
        file_obj = io.BytesIO(final_mapping_string.encode('utf-8'))
        file = discord.File(file_obj, filename="role_mapping.py")
        
        msg = f"✅ 掃描完成。找到了 {found_count} 個對應的身分組。"
        if missing_roles:
            msg += f"\n⚠️ 有 {len(missing_roles)} 個稱號找不到對應的身分組，已在檔案中標記為 None。"
            
        await interaction.response.send_message(msg, file=file, ephemeral=True)
        
async def setup(bot):
    await bot.add_cog(AdminCommands(bot))