import discord
from discord.ext import tasks, commands
import aiohttp
import datetime
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import urllib.parse
import database

# 載入獨立的環境變數檔案
load_dotenv('groq.env')

class DailyNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        default_id = os.getenv("DEFAULT_CHANNEL_ID")
        channel_id_str = database.get_setting("target_channel_id", default=default_id)
        self.target_channel_id = int(channel_id_str) if channel_id_str else 0
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.news_task.start()

    # ==========================================
    # 輔助函式：非同步獲取網頁內文並清洗 HTML
    # ==========================================
    async def fetch_web_content(self, session, url):
        try:
            async with session.get(url, allow_redirects=True, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                return text[:1500]
        except Exception as e:
            print(f"抓取內文失敗: {e}")
            return "（這破網頁本仙法力穿透不了，略過。）"

    # ==========================================
    # 輔助函式：非同步縮網址 (is.gd)
    # ==========================================
    async def get_short_url(self, session, long_url):
        try:
            # 🌟 修正：將長網址進行編碼，避免 Google News 網址內的 & 或 ? 破壞 API 請求
            encoded_url = urllib.parse.quote(long_url, safe='')
            service_url = f"https://is.gd/create.php?format=simple&url={encoded_url}"
            async with session.get(service_url, timeout=5) as res:
                result = (await res.text()).strip()
                
                if result.startswith("http"):
                    return result
                return long_url
        except:
            return long_url

    # ==========================================
    # 排程設定：台灣時間每天早上 8 點 0 分
    # ==========================================
    tz = datetime.timezone(datetime.timedelta(hours=8))
    trigger_time = datetime.time(hour=8, minute=0, tzinfo=tz)

    @tasks.loop(time=trigger_time)
    async def news_task(self):
        current_id = database.get_setting("target_channel_id", default=os.getenv("DEFAULT_CHANNEL_ID"))
        self.target_channel_id = int(current_id) if current_id else self.target_channel_id
        
        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            print("你要本仙人去哪播報新聞又不講清楚")
            return

        if not self.groq_api_key:
            print("本仙人找不到甚麼 GROQ_API_KEY！")
            return

        print("開始執行仙人早報...")
        now_str = datetime.datetime.now(self.tz).strftime("%Y/%m/%d %H:%M")

        async with aiohttp.ClientSession() as session:
            # 1. 抓取 Google 新聞 RSS
            rss_url = "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            try:
                async with session.get(rss_url) as res:
                    xml_data = await res.text()
                    root = ET.fromstring(xml_data)
                    items = root.findall('./channel/item')[:3]
            except Exception as e:
                print(f"抓取 RSS 失敗: {e}")
                return

            news_data = []
            for i, item in enumerate(items):
                title = item.find('title').text
                link = item.find('link').text
                pubDateRaw = item.find('pubDate').text
                
                dt = parsedate_to_datetime(pubDateRaw).astimezone(self.tz)
                pubDate = dt.strftime("%m/%d %H:%M")
                
                # 這裡會取得穩定、正確的短網址
                short_link = await self.get_short_url(session, link)
                full_content = await self.fetch_web_content(session, link)
                
                news_data.append({
                    "id": i + 1,
                    "title": title,
                    "link": short_link,
                    "content": full_content,
                    "date": pubDate
                })

            # 2. 組合給 AI 的資訊
            raw_news_for_ai = "\n\n---\n\n".join([
                f"[新聞 {d['id']}] (發布時間: {d['date']})\n標題: {d['title']}\n內文片段: {d['content']}\n網址: {d['link']}"
                for d in news_data
            ])

            system_prompt = (
                "你是一位名為「雲岫」的摸魚女仙人。你外表大約25歲，性格極度慵懶，人生信條是「能躺著絕不坐著，能喝酒絕不工作」。"
                "你的說話風格：\n"
                "1.隨性吐槽： 帶著看破紅塵的滄桑，覺得凡人爭權奪利很瞎忙。"
                "2.心虛可愛： 雖然嘴巴壞，但如果被抓到在偷懶，會立刻裝得委屈巴巴 (´;ω;`)。"
                "3.生活化： 經常提到想喝酒、腰酸背痛、或是想趕快唸完去曬太陽。"
                "4.豐富表情： 適度使用顏文字來展現那種「厚臉皮」的慵懶感。"
                "請閱讀以下凡間新聞，並以你的視角與口吻撰寫摘要。"
            )
            user_prompt = (
                "請根據以下新聞內容與發布日期，幫我整理一份早報。\n要求：\n"
                "1. 每一則新聞摘要長度約 100 字左右。\n"
                "2. 人設展現： 語氣要慵懶且隨性。要表現出「雖然我很想下班去喝酒，但為了這份微薄的仙俸，我還是勉為其難幫你唸一下」的感覺。\n"
                "3. 結尾多樣化抱怨： 結尾絕對不要重複！請換不同的方式表達你想偷懶、心虛被抓、酒癮發作、或是工作過勞。\n"
                "4. 格式： 開頭標註 [發布時間]，結尾記得先換行再加上網址，使用 Discord Markdown 超連結。\n"
                "   連結文字設定為[點此查看凡塵新聞](網址)\n"
                "5.【極度重要警告】：括號內的網址 必須100%完全複製 我在下方提供的「網址」內容，絕對不准擅自把網址改成 https://www.google.com/ 或其他假網址！\n\n"
            ) + raw_news_for_ai

            # 3. 呼叫 Groq API
            ai_url = "https://api.groq.com/openai/v1/chat/completions"
            ai_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    { "role": "system", "content": system_prompt },
                    { "role": "user", "content": user_prompt }
                ],
                "temperature": 0.5 #
            }
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            try:
                async with session.post(ai_url, headers=headers, json=ai_payload) as ai_res:
                    if ai_res.status == 200:
                        data = await ai_res.json()
                        summary = data['choices'][0]['message']['content']
                    else:
                        raise Exception(f"API Error {ai_res.status}")
            except Exception as e:
                print(f"Groq API 呼叫失敗: {e}")
                summary = "（嘖，這破法術又當機了。本仙懶得重唸，你們自己看這凡間的破事吧，我要去喝酒了）：\n\n" + \
                          "\n".join([f"[{d['date']}] {d['title']}\n{d['link']}" for d in news_data])

            # 4. 準備發送到 Discord 的內容
            final_content = f"🔔 **凡間時辰：{now_str}**\n\n🍶 **仙人晨間碎念 | 凡間瑣事錄**\n\n{summary}"
            if len(final_content) > 1950:
                final_content = final_content[:1900] + "\n\n...（太長了，本仙寫到手痠，剩下的你們自己參悟）"

            # 5. 動態 Webhook 發送邏輯
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name="仙人早報")
            
            if not webhook:
                webhook = await channel.create_webhook(name="仙人早報")

            await webhook.send(
                content=final_content,
                username="摸魚仙人 雲岫",
                avatar_url="https://i.pinimg.com/736x/4d/8e/fa/4d8efa942d7d5ff2ed480eaf2627bace.jpg" 
            )
            print("本仙人要去休息了！")

    @news_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def test_news(self, ctx):
        await self.news_task()
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(DailyNews(bot))