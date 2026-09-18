# 健康打卡機器人 Health Check-in Bot

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.0%2B-blue)](https://discordpy.readthedocs.io/)

## 專案介紹 Introduction

「健康打卡機器人」是一款以 **discord.py** 打造的 Discord 伺服器機器人，把「記得喝水」這件日常小事，包裝成一場帶有等級、連擊與稱號的闖關遊戲。機器人會定時發送提醒、記錄打卡與連續天數、依進度自動發放對應身分組，並額外附上每日運勢籤、解答之書、AI 整理的每日新聞早報等娛樂功能，讓健康提醒不再只是煩人的通知，而是能跟朋友一起累積、互相比較的伺服器日常。整體稱號與世界觀設計參考了熱門戰鬥動漫的能力體系，純屬玩梗包裝，與健康提醒的核心功能無關。

**核心特色**

- 定時健康打卡提醒，搭配連擊（Combo）機制與隨機額外獎勵
- 30 級稱號進度系統，升級自動切換對應身分組
- 下拉選單身分組面板，支援互斥選擇與一鍵卸下
- AI 整理的每日新聞早報（Groq API）
- 娛樂小遊戲：每日運勢籤、解答之書
- 完整的管理員控制面板（頻道設定、數值調整、身分組批次建立等）

---

## 目錄

- [環境需求](#環境需求)
- [安裝方式](#安裝方式)
- [環境變數設定](#環境變數設定)
- [設定身分組](#設定身分組)
- [啟動機器人](#啟動機器人)
- [指令總覽](#指令總覽)
- [遊戲機制](#遊戲機制)
- [資料儲存](#資料儲存)
- [專案結構](#專案結構)
- [安全與權限](#安全與權限)
- [疑難排解](#疑難排解)

---

## 環境需求

- Python 3.8 以上（建議 3.10+）
- pip 套件管理工具
- Discord 伺服器的管理員權限（用於邀請與測試機器人）
- Discord Bot Token（於 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式取得）
- Groq API Key（選用，僅新聞早報功能需要）

確認環境：

```bash
python --version
pip --version
```

---

## 安裝方式

```bash
# 複製專案
git clone <repository_url>
cd discord-water-bot

# 建立虛擬環境（建議）
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# 安裝依賴
pip install -r requirements.txt
```

`requirements.txt` 內容：`discord.py`、`python-dotenv`、`aiohttp`、`beautifulsoup4`。

---

## 環境變數設定

專案不會將任何金鑰寫死在程式碼中，需要自行建立以下兩個檔案（皆已列入 `.gitignore`）。

`.env`（必要）：

| 變數 | 說明 |
| --- | --- |
| `DISCORD_TOKEN` | Discord Bot Token |
| `DEFAULT_CHANNEL_ID` | 開機時預設的訊息發送頻道 ID（可用 `/admin set_channel` 覆蓋） |

`groq.env`（選用，僅新聞早報功能需要）：

| 變數 | 說明 |
| --- | --- |
| `GROQ_API_KEY` | Groq API 金鑰，用於呼叫 `openai/gpt-oss-120b` 模型整理新聞摘要 |

重要：務必確認 `.env` 與 `groq.env` 沒有被提交到版本控制，避免金鑰外洩。

---

## 設定身分組

等級對應的 30 個身分組需要在你自己的伺服器中建立，`constants.py` 中的 `ROLE_MAPPING` 才能對上正確的身分組 ID。三種方式擇一：

### 方式 A：自動建立（推薦）

```
/admin create_roles
```

機器人會依 `TITLE_DATA` 自動建立 30 個身分組，並回傳一份 `role_mapping.py`，將內容複製回 `constants.py` 的 `ROLE_MAPPING` 即可。

### 方式 B：自動掃描既有身分組

```
/admin generate_mapping
```

依稱號名稱在伺服器現有身分組中比對，產生對應的 `role_mapping.py`；找不到的稱號會標記為 `None`。

### 方式 C：手動編輯

直接修改 `constants.py` 的 `ROLE_MAPPING`：

```python
ROLE_MAPPING = {
    1: 1234567890,
    2: 1234567891,
    # ... 以此類推到 30
}
```

---

## 啟動機器人

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

機器人首次加入新伺服器時，會在系統頻道（或第一個有發言權限的文字頻道）自動發送一則角色扮演口吻的自我介紹訊息，內容可用 `/admin test_welcome` 重新觸發預覽。

---

## 指令總覽

### 一般使用者指令

| 指令 | 說明 |
| --- | --- |
| `/rank` | 查看個人健康打卡等級與經驗值進度 |
| `/leaderboard [page]` | 查看伺服器排行榜，支援分頁 |
| `/today` | 查看今日打卡總結與機緣明細 |
| `/ask_book [question]` | 從解答之書隨機抽取一則回覆 |
| `/omikuji` | 抽取今日運勢籤 |
| `/role_ui spawn <標題> <身分組1> [身分組2~5]` | 建立身分組領取下拉選單（需管理身分組權限） |

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

---

## 遊戲機制

### 打卡提醒排程

- 台灣時間每天 10:00 到隔日 02:00，每 30 分鐘發送一則提醒（按鈕互動打卡，防止重複領取）
- 凌晨 00:00～04:00 之間，若連續多回合無人打卡（02:00 後累積 3 回合，或任何時段累積 5 回合），會提前結算並進入睡眠模式，直到隔日 10:00 自動恢復
- 睡眠模式期間會出現「我要睡覺了」按鈕，供使用者查看個人今日總結

### 經驗值與連擊（Combo）

- 每次打卡基礎 +10 EXP，並有機率觸發隨機機緣事件（受當日運勢籤影響機率）
- 連續打卡累積 Combo，每達到 5 的倍數額外 +5 EXP；若打卡中斷（跳過回合）則 Combo 歸零重算
- 升級所需經驗值：`EXP = 15 × 等級² + 50 × 等級 + 50`
- 共 30 個等級，各自對應獨特稱號與身分組顏色（`constants.py` 中的 `TITLE_DATA`）

### 每日結算

- 台灣時間每天 04:00 自動發送排行榜總結（含今日進步最快玩家），並重置每日經驗值統計
- 若當晚提早進入睡眠模式，會直接觸發當次結算，不等到 04:00

### 每日新聞早報

- 台灣時間每天 08:00 自動抓取 Google 新聞（台灣）前 3 則
- 透過 Groq API 呼叫 `openai/gpt-oss-120b` 模型，以固定人設語氣整理成約 100 字摘要
- 使用 `is.gd` 縮短新聞連結，並透過動態建立的 Webhook 發送
- 可用 `/admin trigger_news` 立即觸發一次，不需等待排程

---

## 資料儲存

資料庫為單一 SQLite 檔案 `water_exp.db`，首次執行 `python main.py` 時由 `database.py` 自動建立所有表格；日後新增欄位也會自動補上，不需額外的遷移工具。

| 資料表 | 用途 |
| --- | --- |
| `users` | 使用者的總經驗值、Combo、最後打卡回合／日期、今日經驗、今日運勢籤 |
| `claims` | 打卡防重複領取紀錄（每則提醒訊息 + 使用者僅能領取一次） |
| `daily_events` | 今日經驗值變動明細（供 `/today` 顯示，每日結算後清空） |
| `system_state` | 系統狀態鍵值（目標頻道、目前回合數、連續未打卡次數、是否進入睡眠模式等） |
| `reaction_roles` | 保留欄位，目前尚未串接任何功能 |

其他資料檔案（JSON，可直接編輯擴充）：

| 檔案 | 用途 |
| --- | --- |
| `water_messages.json` | 打卡提醒的隨機文字範本 |
| `fortune.json` | 每日運勢籤的籤詩與解籤內容 |
| `answers.json` | 解答之書的中英雙語回答庫 |
| `events.json` | 打卡時觸發的隨機機緣事件與權重設定 |

---

## 專案結構

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
├── water_exp.db               # SQLite 資料庫（需自行產生，已列入 .gitignore）
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

---

## 安全與權限

### 金鑰管理

- 不在程式碼中硬編碼 Token 或 API Key，一律透過 `.env` / `groq.env` 讀取
- `.env`、`groq.env`、`*.db` 皆已列入 `.gitignore`，請勿手動強制加入版本控制
- 若 Token 或金鑰不慎外洩，請立即在 Discord Developer Portal / Groq 後台重新產生

### 指令權限

| 指令範圍 | 所需權限 |
| --- | --- |
| `/rank`、`/leaderboard`、`/today`、`/ask_book`、`/omikuji` | 無，所有使用者可用 |
| `/role_ui spawn` | 管理身分組 |
| `/admin *` | 伺服器管理員 |

### 機器人所需 Discord 權限

傳送訊息、嵌入連結、管理身分組、建立 Webhook、管理訊息。

### 高風險操作

`/admin remove_user`（不可復原地刪除使用者資料）與 `/admin backup_db`（匯出完整資料庫，含所有使用者數據）僅限管理員使用，請自行評估是否需要進一步限縮權限。

---

## 疑難排解

### 機器人啟動後沒有任何反應 / 斜線指令沒有出現

確認 `.env` 中的 `DISCORD_TOKEN` 正確，且啟動時終端機有印出「斜線指令同步完成」。斜線指令在 Discord 用戶端可能需要數分鐘才會完全同步，或嘗試重新整理 Discord 用戶端。

### 提醒訊息、排行榜或新聞早報沒有發送到預期頻道

檢查是否已設定 `DEFAULT_CHANNEL_ID`，或在目標頻道執行過 `/admin set_channel`；資料庫中的設定會覆蓋 `.env` 預設值。

### 新聞早報沒有反應

確認 `groq.env` 內的 `GROQ_API_KEY` 是否存在且有效；沒有設定時新聞模組會在終端機印出提示並跳過該次排程，可用 `/admin trigger_news` 手動測試。

### 身分組沒有正確發放

確認已透過 `/admin create_roles` 或 `/admin generate_mapping` 產生正確的 `ROLE_MAPPING`，並確認機器人的身分組位置高於欲發放的目標身分組。可用 `/admin sync_level` 對單一使用者重新校準。

### 想清空測試資料重新開始

刪除本機的 `water_exp.db` 後重新啟動機器人，會依 `database.py` 的邏輯重新建立乾淨的資料表。
