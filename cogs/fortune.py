import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
import asyncio

# ==========================================
# 建立專屬於抽籤的 UI 介面 (按鈕)
# ==========================================
class FortuneView(discord.ui.View):
    def __init__(self, author_id: int, fortune_cog):
        super().__init__(timeout=600)
        self.author_id = author_id
        self.fortune_cog = fortune_cog
        self.message = None

    @discord.ui.button(label="我不信！重抽！重抽！重抽！", style=discord.ButtonStyle.secondary, emoji="🫠")
    async def redraw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 檢查：防止其他路人點擊你的重抽按鈕
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❓這是別人的籤筒，你想幹嘛", ephemeral=True)
            return

        # ==========================================
        # 🌟 階段一：仙人的隨機嘲諷語錄庫（擴充版）
        # ==========================================
        taunts = [
            "**摸魚仙人打了個哈欠：**\n「🙄呵，你不是想重抽，你只是想看到滿意的結果吧。」",
            "**摸魚仙人翻了個白眼：**\n「🙄凡人就是難伺候，抽到凶也是命，非要逆天改命嗎？」",
            "**摸魚仙人喝了口茶：**\n「😒逆天改命可是要耗費本座修為的... 算了，這次免費。」",
            "**摸魚仙人不耐煩地揮了揮拂塵：**\n「🙄你以為籤筒是你家開的嗎？快抽快抽，別打擾本座摸魚。」",
            "**摸魚仙人冷笑一聲：**\n「🙄洗牌重抽？凡間的規矩真多，看好了，這可是最後一次。」",
            "**摸魚仙人掏了掏耳朵：**\n「🙄剛剛那支籤不好嗎？我看是你命格太硬，連籤筒都嫌棄你。」",
            "**摸魚仙人看著遠方的雲：**\n「🙄重抽可以，但如果你這次抽到更爛的，可別在本座面前哭天搶地。」",
            "**摸魚仙人優雅地伸了個懶腰：**\n「😒雖然本座時間很多，但也不是用來陪你玩這種『抽到好為止』的遊戲的。」",
            "**摸魚仙人敲了敲桌子：**\n「🙄機緣這種事，求的是第一直覺，你這是在搞批發嗎？」",
            "**摸魚仙人撇了撇嘴：**\n「😒既然不信命，那你還來求籤做什麼？直接回家睡覺不是更快？」",
            "**摸魚仙人嘆了口氣：**\n「🙄本座這拂塵都要揮斷了，你到底要把這點運氣透支到什麼時候？」",
            "**摸魚仙人斜眼看著你：**\n「🙄趕緊抽完滾蛋。」",
            "**摸魚仙人換了個坐姿：**\n「🙄你是想抽籤，還是想透過抽籤來自我催眠？本座看是後者。」",
            "**摸魚仙人揉了揉太陽穴：**\n「🙄凡人的執念啊，就像這煙火，繁瑣又沒什麼實際用途。」",
            "**摸魚仙人沒好氣地說：**\n「🙄再抽下去，這籤筒都要起火了，你這手氣真是不敢恭維。」",
            "**摸魚仙人彈了一下指甲：**\n「🙄本座要是你，現在就轉身走人，免得下一支籤讓你更心碎。」",
            "**摸魚仙人瞇起眼睛：**\n「😒你這是不信神，還是不信邪？」",
            "**摸魚仙人打了個響指：**\n「🙄最後一次！再囉嗦本座就去午睡了，天王老子來都沒用。」",
            "**摸魚仙人看著你手中的籤：**\n「😒執迷不悟。」",
            "**摸魚仙人呵呵一笑：**\n「😒你是不是覺得，只要抽得夠快，不幸就追不上你？」",
            "**摸魚仙人托著下巴：**\n「😒這屆凡人真難帶，連抽個籤都要貨比三家，當本座是代購嗎？」",
            "**摸魚仙人打了個噴嚏：**\n「😒有人在念叨本座... 肯定是你這傢伙心存怨念，快重抽，少廢話。」",
            "**摸魚仙人指了指天空：**\n「🙄老天爺都看累了，本座也看累了。」",
            "**摸魚仙人神情慵懶：**\n「🙄強扭的瓜不甜，強求的籤不靈。但既然你堅持，本座就隨便你吧。」"
        ]
        
        # 隨機抽取一句嘲諷
        selected_taunt = random.choice(taunts)
        
        # 覆寫畫面，顯示嘲諷並隱藏原本的籤詩與按鈕
        await interaction.response.edit_message(content=selected_taunt, embed=None, view=None)

        # ==========================================
        # 🌟 階段二：等待演出時間
        # ==========================================
        # 讓畫面停留在嘲諷訊息 2.5 秒
        await asyncio.sleep(2.5)

        # ==========================================
        # 🌟 階段三：抽出新籤並再次更新畫面
        # ==========================================
        new_embed = self.fortune_cog.get_random_fortune_embed()
        
        if new_embed:
            # 重新放入 embed，並把 view=self 放回去讓按鈕重新出現
            await interaction.edit_original_response(content=None, embed=new_embed, view=self)
        else:
            await interaction.edit_original_response(content="🙄看吧，非得逆天改命。", embed=None, view=None)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

# ==========================================
# 運勢系統主類別
# ==========================================
class Fortune(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fortunes_data = []
        self.load_fortunes()

    def load_fortunes(self):
        file_path = "fortune.json" 
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.fortunes_data = json.load(f)
                print(f"✅ 成功載入 {len(self.fortunes_data)} 筆運勢籤詩。")
            else:
                print(f"❌ 找不到 {file_path} 檔案，請確認路徑。")
        except json.JSONDecodeError as e:
            print(f"❌ fortune.json 格式錯誤: {e}")
        except Exception as e:
            print(f"❌ 讀取 fortune.json 時發生未知錯誤: {e}")

    def get_color(self, f_type):
        mapping = {
            "大吉": 0xE74C3C, "吉": 0xF1C40F, "小吉": 0x2ECC71,
            "末吉": 0x3498DB, "末小吉": 0x95A5A6, "兇": 0x2C3E50
        }
        return mapping.get(f_type, 0xFFFFFF)

    def get_random_fortune_embed(self):
        if not self.fortunes_data:
            return None
            
        drawn_fortune = random.choice(self.fortunes_data)
        embed_color = self.get_color(drawn_fortune.get("type", ""))
        
        embed = discord.Embed(
            title=f"⛩️ 摸魚仙人賜籤：【 {drawn_fortune['type']} 】", 
            color=embed_color
        )
        
        embed.add_field(name="📜 籤詩", value=f"*{drawn_fortune['poem']}*", inline=False)
        embed.add_field(name="💡 仙人解惑", value=drawn_fortune['explain'], inline=False)

        result_dict = drawn_fortune.get("result", {})
        if result_dict:
            result_lines = [f"**{k}**：{v}" for k, v in result_dict.items()]
            result_text = "\n".join(result_lines)
            embed.add_field(name="✨ 細項指引", value=result_text, inline=False)

        if "note" in drawn_fortune and drawn_fortune["note"]:
            embed.set_footer(text=f"仙人叮囑：{drawn_fortune['note']}")

        return embed

    @app_commands.command(name="omikuji", description="向摸魚仙人求取一支今日運勢籤")
    async def omikuji(self, interaction: discord.Interaction):
        if not self.fortunes_data:
            await interaction.response.send_message("🫩摸魚仙人昨天喝太多，還有點酒醉，目前找不到籤筒", ephemeral=True)
            return

        embed = self.get_random_fortune_embed()
        
        if embed:
            # 實例化帶有重抽按鈕的介面
            view = FortuneView(interaction.user.id, self)
            await interaction.response.send_message(embed=embed, view=view)
            
            # 將發送後的訊息物件儲存進 view 中，以便未來 timeout 時更新狀態
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message("🫩摸魚仙人昨天喝太多，好像把籤筒給丟啦", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Fortune(bot))