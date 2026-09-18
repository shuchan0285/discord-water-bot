# 健康打卡機器人 Health Check-in Bot

健康打卡機器人是一款以 **discord.py** 打造的 Discord 伺服器機器人，把「記得喝水」這件日常小事包裝成帶有等級、連擊與稱號的闖關遊戲。它會在伺服器內定時發送提醒、記錄打卡與連續天數、依進度自動發放對應身分組，並附上每日運勢籤、解答之書、AI 新聞早報等幾個小遊戲，讓健康提醒不再只是通知，而是能跟朋友一起累積、互相比較的伺服器日常。稱號與世界觀命名參考了熱門戰鬥動漫的能力體系，純屬玩梗包裝，不影響任何實際打卡邏輯。

這個專案是為單一 Discord 伺服器設計的自架機器人，資料存放在本機的一個 SQLite 檔案中。它不是多租戶服務，沒有網頁後台，也不需要對外開放連接埠；只要有 Bot Token（以及選用的 Groq API Key）就能在自己的電腦或伺服器上執行。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.0%2B-blue)

## Key Features / 核心特色

- 台灣時間每天 10:00 至隔日 02:00，每 30 分鐘發送一次健康打卡提醒，透過按鈕互動領取，並自動防止重複領取。
- 連擊（Combo）機制與隨機機緣事件，連續打卡可額外獲得經驗值加成。
- 30 級稱號進度系統，升級時自動移除舊身分組並發放新身分組。
- 下拉選單身分組面板，支援最多 5 個互斥選項與一鍵卸下。
- 每日運勢籤（含重抽與化解機制）與解答之書兩個娛樂小遊戲，皆為互動式按鈕流程。
- 透過 Groq API（`openai/gpt-oss-120b`）自動整理的每日新聞早報，以固定人設語氣撰寫摘要並經動態 Webhook 發送。
- 完整的 `/admin` 管理面板：頻道設定、經驗值調整、資料庫備份、身分組批次建立與校準。

## Requirements

- Python 3.8 以上（建議 3.10+）
- pip
- Discord 伺服器的管理員權限，用於邀請與測試機器人
- Discord Bot Token，於 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式取得
- Groq API Key（選用，僅新聞早報功能需要）

確認環境：

```bash
python --version
pip --version
```

## Installation

```bash
git clone <repository_url>
cd discord-water-bot
```

建立虛擬環境（建議）：

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux
```

安裝依賴：

```bash
pip install -r requirements.txt
```

`requirements.txt` 內容：`discord.py`、`python-dotenv`、`aiohttp`、`beautifulsoup4`。

## Configuration

機器人不會將任何金鑰寫死在程式碼中，設定一律透過環境變數讀取。這兩個檔案都需要自行建立，且已列入 `.gitignore`：

`.env`（必要）：

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `DISCORD_TOKEN` | 無 | Discord Bot Token |
| `DEFAULT_CHANNEL_ID` | 無 | 開機時預設的訊息發送頻道 ID，可用 `/admin set_channel` 在資料庫中覆蓋 |

`groq.env`（選用，僅新聞早報功能需要）：

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `GROQ_API_KEY` | 無 | 呼叫 Groq API（`openai/gpt-oss-120b`）整理新聞摘要用的金鑰 |

未設定 `GROQ_API_KEY` 時，新聞早報排程會在終端機印出提示並直接跳過該次執行，其餘功能不受影響。

## Usage

啟動機器人：

```bash
python main.py
```

看到以下輸出即代表啟動成功：

```
資料庫初始化完成
已載入模組: cogs.xxx
已載入模組: cogs.yyy
斜線指令同步完成
Bot 已經成功登入為 YourBotName#0000
```

機器人首次加入新伺服器時，會在系統頻道（或第一個有發言權限的文字頻道）自動發送一則角色扮演口吻的自我介紹訊息，可用 `/admin test_welcome` 重新觸發預覽。

### 設定等級身分組

30 個等級稱號需要在自己的伺服器中建立對應身分組，`constants.py` 的 `ROLE_MAPPING` 才能對上正確的身分組 ID，三種方式擇一：

1. **自動建立（推薦）**：執行 `/admin create_roles`，機器人會依 `TITLE_DATA` 批次建立 30 個身分組，並回傳一份 `role_mapping.py`，將內容複製回 `constants.py` 即可。
2. **自動掃描既有身分組**：執行 `/admin generate_mapping`，依稱號名稱在伺服器現有身分組中比對；找不到的稱號會在產生的檔案中標記為 `None`。
3. **手動編輯**：直接修改 `constants.py` 的 `ROLE_MAPPING` 字典，把每個等級的假 ID 換成實際身分組 ID。

### 打卡與睡眠模式

使用者點擊提醒訊息上的按鈕即完成一次打卡，取得基礎經驗值並可能觸發隨機機緣。凌晨 00:00～04:00 之間，若連續多回合無人打卡（02:00 後累積 3 回合，或任何時段累積 5 回合），系統會提前結算並進入睡眠模式，直到隔日 10:00 自動恢復；睡眠模式期間提醒訊息會附上「我要睡覺了」按鈕，供使用者查看個人今日總結。

### 身分組下拉選單

管理身分組權限的使用者可執行：

```
/role_ui spawn <標題> <@身分組1> [身分組2~5]
```

會在目前頻道建立一個最多 5 選項的下拉選單面板，選擇項目彼此互斥，清空選單即可卸下該面板發放的身分組。

## Common Commands

### 一般使用者指令

| 指令 | 說明 |
| --- | --- |
| `/rank` | 查看個人健康打卡等級與經驗值進度 |
| `/leaderboard [page]` | 查看伺服器排行榜，支援分頁 |
| `/today` | 查看今日打卡總結與機緣明細 |
| `/ask_book [question]` | 從解答之書隨機抽取一則回覆 |
| `/omikuji` | 抽取今日運勢籤 |

### 管理員指令（`/admin`，需伺服器管理員權限）

| 指令 | 說明 |
| --- | --- |
| `/admin set_channel [channel]` | 設定提醒／排行榜／新聞早報的目標頻道 |
| `/admin check <member>` | 查詢使用者的等級、經驗值、連擊等後台數據 |
| `/admin add_exp <member> <amount>` | 增加或扣除（負數）使用者經驗值 |
| `/admin set_exp <member> <amount>` | 強制設定使用者的最終經驗值 |
| `/admin reset <member>` | 將使用者經驗值、連擊、回合數歸零（保留打卡紀錄） |
| `/admin reset_daily <member>` | 清空使用者今日打卡狀態，可重新觸發今日首抽 |
| `/admin sync_level <member>` | 依目前經驗值重新校準身分組 |
| `/admin remove_user <member>` | 徹底刪除使用者所有資料（不可復原） |
| `/admin backup_db` | 下載目前資料庫檔案備份 |
| `/admin trigger_water` | 立即手動發送一則打卡通知 |
| `/admin toggle_water <start\|stop>` | 啟動或停止自動提醒排程 |
| `/admin trigger_news` | 立即執行一次新聞早報 |
| `/admin clear [amount]` | 清理目前頻道內指定數量的訊息 |
| `/admin create_roles` | 批次建立 30 個等級身分組並產生 Mapping |
| `/admin generate_mapping` | 掃描既有身分組並產生 Mapping |
| `/admin test_welcome` | 重新觸發加入伺服器時的歡迎訊息 |

## Limitations and Notes

- 設計給單一 Discord 伺服器使用；沒有多伺服器隔離，`target_channel_id` 等設定是全域的一組值，同一個機器人跨多伺服器執行時會共用同一個目標頻道。
- 沒有網頁後台，所有管理操作都透過 Discord 斜線指令完成。
- 經驗值等級公式與提醒排程時間目前寫死在程式碼中（`database.py`、`cogs/water_reminder.py`），不是可透過環境變數調整的設定。
- 資料庫是單一 SQLite 檔案 `water_exp.db`，沒有備份排程，僅能透過 `/admin backup_db` 手動下載；直接刪除該檔案會清空所有使用者資料並在下次啟動時重建空表。
- `/admin remove_user` 與 `/admin reset` 皆為不可復原操作，請謹慎使用。
- 新聞早報依賴 Google News RSS 與 Groq API 的外部服務可用性，其中一方異常時該次排程會直接跳過或退回未整理的原始新聞連結。

## Project Structure

```
discord-water-bot/
├── main.py                  # Bot 主程式進入點
├── constants.py              # 等級稱號、身分組 ID 對照表
├── database.py               # SQLite 初始化與所有資料庫操作
├── event_manager.py          # 打卡隨機機緣事件抽取邏輯
│
├── cogs/                     # Discord.py 功能模組
│   ├── water_reminder.py     # 打卡提醒排程、睡眠模式、按鈕互動
│   ├── level_system.py       # 等級查詢、排行榜、每日結算
│   ├── admin.py               # 管理員控制面板
│   ├── answer_book.py         # 解答之書
│   ├── fortune.py             # 每日運勢籤
│   ├── daily_news.py          # AI 新聞早報
│   └── reaction_roles.py      # 身分組下拉選單
│
├── water_exp.db               # SQLite 資料庫（自動產生，已列入 .gitignore）
├── water_messages.json        # 打卡提醒文字範本
├── fortune.json                # 運勢籤資料
├── answers.json                 # 解答之書資料
├── events.json                  # 隨機機緣事件設定
│
├── .env                        # Discord Token（需自行建立）
├── groq.env                    # Groq API Key（需自行建立）
├── requirements.txt
├── .gitignore
└── README.md
```

## Data Overview

沒有對外的 HTTP API，所有資料都存在本機檔案中。

### SQLite（`water_exp.db`）

| 資料表 | 用途 |
| --- | --- |
| `users` | 使用者的總經驗值、Combo、最後打卡回合／日期、今日經驗、今日運勢籤 |
| `claims` | 打卡防重複領取紀錄（每則提醒訊息 + 使用者僅能領取一次） |
| `daily_events` | 今日經驗值變動明細，供 `/today` 顯示，每日結算後清空 |
| `system_state` | 系統狀態鍵值：目標頻道、目前回合數、連續未打卡次數、是否進入睡眠模式等 |
| `reaction_roles` | 保留欄位，目前尚未串接任何功能 |

### JSON 設定檔（可直接編輯擴充）

| 檔案 | 用途 |
| --- | --- |
| `water_messages.json` | 打卡提醒的隨機文字範本 |
| `fortune.json` | 每日運勢籤的籤詩與解籤內容 |
| `answers.json` | 解答之書的中英雙語回答庫 |
| `events.json` | 打卡時觸發的隨機機緣事件與權重設定 |

## Troubleshooting

### 機器人啟動後沒有任何反應，或斜線指令沒有出現

確認 `.env` 中的 `DISCORD_TOKEN` 正確，且啟動時終端機有印出「斜線指令同步完成」。斜線指令在 Discord 用戶端有時需要數分鐘才會完全同步，可嘗試重新整理用戶端。

### 提醒訊息、排行榜或新聞早報沒有發送到預期頻道

檢查是否已設定 `DEFAULT_CHANNEL_ID`，或在目標頻道執行過 `/admin set_channel`；資料庫中的設定會覆蓋 `.env` 的預設值。

### 新聞早報沒有反應

確認 `groq.env` 內的 `GROQ_API_KEY` 是否存在且有效；未設定時新聞模組會在終端機印出提示並跳過該次排程，可用 `/admin trigger_news` 手動測試。

### 身分組沒有正確發放

確認已透過 `/admin create_roles` 或 `/admin generate_mapping` 產生正確的 `ROLE_MAPPING`，並確認機器人的身分組位置高於欲發放的目標身分組。可用 `/admin sync_level` 對單一使用者重新校準。

### 想清空測試資料重新開始

刪除本機的 `water_exp.db` 後重新啟動機器人，`database.py` 會依原本的邏輯重新建立乾淨的資料表。
