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

# 載入獨立的環境變數檔案
load_dotenv('groq.env')

class DailyNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ⚠️ 請在此指定你要發送新聞的「頻道 ID」
        self.target_channel_id = 1491748943690993875 
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.news_task.start()

    # ==========================================
    # 輔助函式：非同步獲取網頁內文並清洗 HTML
    # ==========================================
    async def fetch_web_content(self, session, url):
        try:
            async with session.get(url, allow_redirects=True, timeout=10) as response:
                html = await response.text()
                # 使用 BeautifulSoup 清洗 HTML，比正則表達式更安全穩定
                soup = BeautifulSoup(html, "html.parser")
                # 移除 script 與 style 標籤
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                return text[:1500]
        except Exception as e:
            print(f"抓取內文失敗: {e}")
            return "無法讀取內容喵。"

    # ==========================================
    # 輔助函式：非同步縮網址 (is.gd)
    # ==========================================
    async def get_short_url(self, session, long_url):
        try:
            service_url = f"https://is.gd/create.php?format=simple&url={long_url}"
            async with session.get(service_url, timeout=5) as res:
                return (await res.text()).strip()
        except:
            return long_url

    # ==========================================
    # 排程設定：台灣時間每天早上 8 點 0 分
    # ==========================================
    tz = datetime.timezone(datetime.timedelta(hours=8))
    trigger_time = datetime.time(hour=8, minute=0, tzinfo=tz)

    @tasks.loop(time=trigger_time)
    async def news_task(self):
        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            print("新聞模組找不到指定的頻道！")
            return

        if not self.groq_api_key:
            print("找不到 GROQ_API_KEY，請檢查 groq.env 設定！")
            return

        print("開始執行貓咪早報任務...")
        now_str = datetime.datetime.now(self.tz).strftime("%Y/%m/%d %H:%M")

        # 使用 aiohttp 開啟非同步連線池
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
                
                # 轉換 RSS 的日期格式為自訂格式
                dt = parsedate_to_datetime(pubDateRaw).astimezone(self.tz)
                pubDate = dt.strftime("%m/%d %H:%M")
                
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

            system_prompt = "你是一位住在 Discord 伺服器裡的可愛『貓咪』。請閱讀新聞內文與發布日期，為每則新聞撰寫約 100 字的深入摘要。"
            user_prompt = (
                "請根據以下新聞內容與發布日期，整理一份摘要。\n要求：\n"
                "1. 每一則新聞摘要長度約 100 字左右。\n"
                "2. 語氣要像親切的貓咪，多用『喵』。\n"
                "3. 摘要開頭請務必標註新聞的發布時間 (例如：[04/09 10:00])。\n"
                "4. 每則摘要最後必須換行附上該則新聞的 [縮址]。\n\n"
            ) + raw_news_for_ai

            # 3. 呼叫 Groq API
            ai_url = "https://api.groq.com/openai/v1/chat/completions"
            ai_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    { "role": "system", "content": system_prompt },
                    { "role": "user", "content": user_prompt }
                ],
                "temperature": 0.5
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
                summary = "（喵嗚... 讀報時頭好暈喵... 這裡是快速連結喵）：\n\n" + \
                          "\n".join([f"[{d['date']}] {d['title']}\n{d['link']}" for d in news_data])

            # 4. 準備發送到 Discord 的內容
            final_content = f"🔔 **現在時間：{now_str}**\n\n🐈 **貓咪早安讀報 | 今日新聞摘要**\n\n{summary}"
            if len(final_content) > 1950:
                final_content = final_content[:1900] + "\n\n...(太長了喵)"

            # 5. 動態 Webhook 發送邏輯 (核心亮點)
            # 讓機器人自動在目標頻道尋找名為「貓咪早報」的 Webhook，找不到就自動建立一個
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name="貓咪早報")
            
            if not webhook:
                webhook = await channel.create_webhook(name="貓咪早報")

            # 使用 Webhook 發送訊息，套用自訂的貓咪名稱與大頭貼
            await webhook.send(
                content=final_content,
                username="貓咪早報",
                avatar_url="https://share99.com/wp-content/uploads/2020/07/30bc2670cf274f6a687b081fb09a898c.jpg"
            )
            print("新聞發送完畢！")

    @news_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

    # 測試用指令：輸入 !test_news 可以立刻觸發早報，測試完可刪除
    @commands.command()
    async def test_news(self, ctx):
        await self.news_task()
        await ctx.message.delete() # 刪除你輸入的指令

async def setup(bot):
    await bot.add_cog(DailyNews(bot))