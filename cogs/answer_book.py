# cogs/answer_book.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
import asyncio

class AnswerBook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.answers_data = {}
        self.load_answers()

    def load_answers(self):
        file_path = "answers.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.answers_data = json.load(f)
                print(f"成功載入 {len(self.answers_data)} 筆解答之書內容。")
            else:
                print(f"找不到 {file_path} 檔案，請確認路徑。")
        except json.JSONDecodeError as e:
            print(f"answers.json 格式錯誤: {e}")
        except Exception as e:
            print(f"讀取 answers.json 時發生未知錯誤: {e}")

    @app_commands.command(name="ask_book", description="在心中默念問題，或輸入下來，讓摸魚仙人翻閱解答之書")
    @app_commands.describe(question="你的問題 (可不填，在心中默念即可)")
    async def ask_book(self, interaction: discord.Interaction, question: str = None):
        if not self.answers_data:
            await interaction.response.send_message("摸魚仙人昨天喝太多，還在找解答之書在哪", ephemeral=True)
            return

        # 先在背景抽出答案，並取得 meta 中的 tone (語氣)
        drawn_block = random.choice(list(self.answers_data.values()))
        zh_answer = drawn_block.get("answer", {}).get("zh-TW", "無字天書...")
        en_answer = drawn_block.get("answer", {}).get("en", "No answer...")

        # 如果沒有 tone 標籤，預設為 neutral (中立)
        tone = drawn_block.get("meta", {}).get("tone", "neutral")

        # ==========================================
        # 階段一：翻書的過場動畫
        # ==========================================
        opening_msg = "**摸魚仙人打了個哈欠，隨手翻開厚重的《解答之書》...**"
        if question:
            opening_msg = f"**你的問題：**「{question}」\n\n{opening_msg}"

        await interaction.response.send_message(content=opening_msg)

        # ==========================================
        # 階段二：等待演出時間
        # ==========================================
        await asyncio.sleep(2.5)

        # ==========================================
        # 階段三：依據語氣 (tone) 產生專屬嘲諷/引語
        # ==========================================
        # 仙人的語錄庫 (你可以依照 JSON 裡的 tone 自由擴充)
        tone_reactions = {
            "direct": [
                "仙人冷哼一聲，用看透一切的眼神指著書上的一行字：",
                "仙人翻了個大白眼，毫不留情地念出：",
                "仙人用力敲了敲書本，語氣嚴厲："
            ],
            "gentle": [
                "仙人微微一笑，拂塵輕掃過頁面，輕聲說道：",
                "仙人吹了吹茶上的熱氣，溫和地給出指引：",
                "仙人眼神難得柔和，緩緩念出這段文字："
            ],
            "mysterious": [
                "仙人半瞇著眼，掐指一算，幽幽地看著書面：",
                "周圍的空氣突然安靜，仙人神秘兮兮地說：",
                "仙人摸了摸下巴，若有所思地留下這句話："
            ],
            "neutral": [
                "仙人平靜地看著書頁，毫無波瀾地讀出：",
                "仙人打了個哈欠，隨便指了指這一段：",
                "仙人聳聳肩，把厚重的書本推到你面前："
            ]
        }

        # 根據抓取到的 tone，隨機選一句仙人的動作。若找不到對應的 tone，就用 neutral。
        reactions = tone_reactions.get(tone, tone_reactions["neutral"])
        reaction_text = random.choice(reactions)

        # ==========================================
        # 階段四：更新畫面
        # ==========================================
        embed = discord.Embed(
            title="解答之書的指引",
            description=f"**{reaction_text}**\n\n# 「{zh_answer}」\n*{en_answer}*",
            color=0x93A2B7
        )

        if question:
            embed.set_author(name=f"問題：{question}", icon_url=interaction.user.display_avatar.url)

        await interaction.edit_original_response(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(AnswerBook(bot))