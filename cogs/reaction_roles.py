import discord
from discord.ext import commands
from discord import app_commands

class RoleUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ui_group = app_commands.Group(
        name="role_ui", 
        description="UI 下拉選單身分組派發系統",
        default_permissions=discord.Permissions(manage_roles=True)
    )

    # ==========================================
    # 指令：產生下拉選單面板
    # ==========================================
    @ui_group.command(name="spawn", description="在當前頻道建立一個身分組領取下拉選單 (最多支援 5 個選項)")
    @app_commands.describe(
        title="選單面板的標題訊息",
        role1="選項 1", role2="選項 2 (選填)", role3="選項 3 (選填)", role4="選項 4 (選填)", role5="選項 5 (選填)"
    )
    async def spawn_menu(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        role1: discord.Role, 
        role2: discord.Role = None, 
        role3: discord.Role = None, 
        role4: discord.Role = None, 
        role5: discord.Role = None
    ):
        # 整理使用者傳入的角色清單，過濾掉未填寫的 None
        roles = [r for r in [role1, role2, role3, role4, role5] if r is not None]
        
        # 建立選單選項
        options = []
        for role in roles:
            options.append(
                discord.SelectOption(
                    label=role.name, 
                    value=str(role.id), # 將 Role ID 作為選項的值
                    description=f"領取 {role.name} 身分組"
                )
            )

        # 實例化一個基底的 Select 元件
        # min_values=0 允許使用者「取消勾選」來卸下身分組
        # max_values=1 確保互斥，一次只能選一個
        select = discord.ui.Select(
            placeholder="請選擇你要裝備的身分組...",
            min_values=0,
            max_values=1,
            options=options,
            custom_id="dynamic_role_select_menu" # 固定的 ID，供全域監聽器捕捉
        )

        view = discord.ui.View(timeout=None)
        view.add_item(select)

        embed = discord.Embed(title="🏷️ 身分組領取面板", description=title, color=0x2b2d31)
        await interaction.response.send_message(embed=embed, view=view)

    # ==========================================
    # 核心監聽：全域處理下拉選單互動 (無狀態設計)
    # ==========================================
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # 確保這是一個 UI 元件互動，且是我們指定的下拉選單
        if interaction.type != discord.InteractionType.component:
            return
        if interaction.data.get("custom_id") != "dynamic_role_select_menu":
            return

        guild = interaction.guild
        member = interaction.user
        if not guild or not isinstance(member, discord.Member):
            return

        # 取得使用者選擇的 Role ID (若清空選單則為 None)
        selected_values = interaction.data.get("values", [])
        selected_role_id = int(selected_values[0]) if selected_values else None

        # 從互動本身的 UI Payload 中，萃取該選單中所有的 Role ID
        # 用於確保「卸除」不屬於本次選擇的其他互斥身分組
        all_menu_role_ids = []
        for component in interaction.message.components:
            for child in component.children:
                if child.custom_id == "dynamic_role_select_menu":
                    for option in child.options:
                        all_menu_role_ids.append(int(option.value))

        roles_to_add = []
        roles_to_remove = []

        # 執行互斥邏輯判斷
        for r_id in all_menu_role_ids:
            role = guild.get_role(r_id)
            if not role: 
                continue
            
            if selected_role_id and r_id == selected_role_id:
                if role not in member.roles:
                    roles_to_add.append(role)
            else:
                if role in member.roles:
                    roles_to_remove.append(role)

        # 執行權限變更
        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            if roles_to_add:
                await member.add_roles(*roles_to_add)

            # 回覆互動 (Ephemeral 僅自己可見)
            if selected_role_id:
                await interaction.response.send_message(f"✅ 已為你裝備身分組：<@&{selected_role_id}>", ephemeral=True)
            else:
                await interaction.response.send_message("🗑️ 已成功卸下該面板的身分組。", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ 錯誤：機器人權限不足。請確保機器人的身分組位置高於你想派發的身分組。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ 發生未知的系統錯誤：{e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleUI(bot))