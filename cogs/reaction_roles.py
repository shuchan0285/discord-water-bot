import discord
from discord.ext import commands
import database

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def roleReact(self, ctx):
        await ctx.send("使用方式：`!roleReact add <訊息ID> <@身分組> <表情符號>`")

    @roleReact.command()
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, message_id: int, role: discord.Role, emoji: str):
        database.add_reaction_role(message_id, emoji, role.id)
        try:
            msg = await ctx.channel.fetch_message(message_id)
            await msg.add_reaction(emoji)
        except:
            pass
        await ctx.send(f"✅ 設定成功！訊息 {message_id} 的 {emoji} 已綁定為 **{role.name}**")

    # ==========================================
    # 核心監聽：增加反應 (含互斥切換，無通知)
    # ==========================================
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        target_role_id = database.get_role_by_reaction(payload.message_id, str(payload.emoji))
        if not target_role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = await guild.fetch_member(payload.user_id)
        target_role = guild.get_role(target_role_id)

        # 互斥邏輯：找出這則訊息綁定的所有身分組，移除掉不是這次點擊的那些
        all_bindings = database.get_all_roles_for_message(payload.message_id)

        for r_id, emoji_name in all_bindings:
            r_id = int(r_id)
            if r_id != target_role_id:
                old_role = guild.get_role(r_id)
                if old_role in member.roles:
                    # 移除舊身分組
                    await member.remove_roles(old_role)
                    # 同步移除介面上的舊表情符號
                    try:
                        channel = self.bot.get_channel(payload.channel_id)
                        message = await channel.fetch_message(payload.message_id)
                        await message.remove_reaction(emoji_name, member)
                    except:
                        pass

        # 加入新身分組 (不發送任何通知)
        await member.add_roles(target_role)

    # ==========================================
    # 核心監聽：移除反應 (無通知)
    # ==========================================
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        role_id = database.get_role_by_reaction(payload.message_id, str(payload.emoji))
        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        try:
            member = await guild.fetch_member(payload.user_id)
            role = guild.get_role(role_id)
            if role and member:
                # 移除身分組 (不發送任何通知)
                await member.remove_roles(role)
        except Exception as e:
            print(f"收回身分組失敗: {e}")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))