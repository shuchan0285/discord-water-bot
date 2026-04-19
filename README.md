# 🥤 Water Reminder Bot - 喝水提醒機器人

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.0%2B-blue)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一個基於 **Discord.py** 開發的喝水提醒機器人，融合《咒術迴戰》主題設定。透過遊戲化機制鼓勵使用者養成健康的飲水習慣。

**✨ 核心特色**
- 🎮 完整的等級系統與排行榜（30 級咒術迴戰主題）
- 💧 自動化喝水提醒與打卡系統（Combo 機制）
- 🎯 雙模式身分組管理（反應綁定 + 下拉選單）
- 📰 AI 整理的每日新聞早報（Groq Llama 3.3）
- 🎰 娛樂小遊戲（運勢占卜、解答之書）
- 🔑 完整的管理員控制面板

---

## 📑 目錄

- [功能概覽](#-功能概覽)
- [專案結構](#-專案結構)
- [快速開始](#-快速開始)
- [使用指令](#-使用指令)
- [遊戲機制](#-遊戲機制)
- [資料庫結構](#-資料庫結構)
- [配置說明](#-配置說明)
- [安全與權限](#-安全與權限)

---

## ✨ 功能概覽

### 1️⃣ 喝水打卡系統
自動定時發送喝水提醒，鼓勵使用者養成飲水習慣。

| 功能 | 說明 |
|-----|------|
| **定時提醒** | 每天 10:00～23:30，每 30 分鐘發送一次提醒 |
| **互動式打卡** | 使用者點擊按鈕完成打卡，防止重複領取獎勵 |
| **Combo 機制** | 連續打卡觸發 Combo，每 5 Combo 額外獎勵 +5 EXP |
| **自動身分組** | 首次打卡自動獲得 Lv.1 身分組，升級自動更換 |
| **睡眠統計** | 提供「睡前報告」功能，展示一日修行成果 |

### 2️⃣ 等級與排行榜
30 階段咒術迴戰主題的等級系統，每個等級對應獨特稱號與顏色。

| 功能 | 說明 |
|-----|------|
| **30 級系統** | 從「非術師」到「詛咒之王」的完整進度 |
| **經驗值機制** | 公式：`EXP = 50 × 等級 + 50`，需累積超 51,500 EXP 達最高級 |
| **進度條展示** | 使用區塊字符（■□）視覺化展示升級進度 |
| **排行榜查詢** | `/leaderboard` 指令，支援多頁查詢、獎牌符號、彩色身分組 |
| **個人等級查看** | `/rank` 指令，展示詳細的等級與進度資訊 |

### 3️⃣ 身分組系統（雙模式）

#### 模式 A：反應綁定 (Reaction Roles)
```
!roleReact add <訊息ID> <@身分組> <表情符號>
```
- 管理員綁定訊息上的表情符號與身分組
- 採取「互斥」邏輯，選擇一個表情自動移除其他
- 所有綁定規則永久儲存於 SQLite 資料庫

#### 模式 B：下拉選單 UI (Select Menu)
```
/role_ui spawn <標題> <@身分組1> [身分組2~5]
```
- 管理員建立美觀的下拉選單身分組面板
- 支援 1～5 個選項，靈活配置
- 互斥邏輯，使用者可清空選單卸下身分組

### 4️⃣ 管理員控制面板
完整的伺服器管理工具，支援數據查詢、系統控制、身分組管理。

| 指令 | 功能 |
|-----|------|
| `/admin check <使用者>` | 查詢使用者的 EXP、Combo、最後打卡回合 |
| `/admin trigger_water` | 立即發送一則喝水通知 |
| `/admin toggle_water [start\|stop]` | 啟動/停止自動喝水排程 |
| `/admin backup_db` | 下載資料庫備份（`.db` 格式） |
| `/admin remove_user <使用者>` | ⚠️ 完全刪除使用者所有遊戲數據 |
| `/admin create_roles` | 自動建立 30 個身分組並產生 `ROLE_MAPPING` 程式碼 |
| `/admin generate_mapping` | 掃描現有身分組，自動產生 `ROLE_MAPPING` 配置 |
| `/admin test_welcome` | 測試新伺服器歡迎訊息 |

### 5️⃣ 每日新聞模組
使用 AI 自動整理新聞，每日早上 8:00（台灣時間）發送一次摘要。

| 功能 | 說明 |
|-----|------|
| **自動早報** | 每日早上 8:00 自動發送 Google News 台灣新聞摘要 |
| **AI 整理** | 使用 Groq Llama 3.3 70B 模型撰寫深入摘要（~100 字） |
| **RSS 爬蟲** | 自動抓取前 3 則台灣新聞 |
| **網址縮短** | 使用 `is.gd` 服務自動縮短新聞連結 |
| **Webhook 發送** | 動態建立「貓咪早報」Webhook，以可愛貓咪名義發送 |
| **測試模式** | `!test_news` 立即觸發（測試完自動刪除指令） |

### 6️⃣ 解答之書
從龐大的智慧語庫中隨機抽取靈感。

| 功能 | 說明 |
|-----|------|
| **互動式抽籤** | `/ask_book [問題]` 指令隨機抽取回答 |
| **雙語支援** | 內建繁體中文與英文回答 |
| **情感分析** | 根據標籤調整回答語氣（wisdom、humor、ominous 等） |
| **過場動畫** | 仙人翻書與思考的互動式視覺效果 |
| **彈性提問** | 支援有具體問題或在心中默念兩種模式 |
| **易於擴充** | JSON 格式儲存，輕鬆新增回答 |

### 7️⃣ 幸運抽籤
摸魚仙人為你占卜每日運勢。

| 功能 | 說明 |
|-----|------|
| **運勢占卜** | `/fortune` 指令進行每日運勢抽籤 |
| **七個等級** | 大吉、中吉、小吉、平、小凶、中凶、大凶 |
| **仙人互動** | 摸魚仙人以詼諧風趣的語調引導過程 |
| **重抽機制** | 點擊「重抽」按鈕獲得隨機嘲諷語錄（限時 10 分鐘） |
| **彩色展示** | 根據運勢等級自動調整訊息顏色 |
| **個人化建議** | 針對愛情、財運、學業、工作提供運勢詳解 |

---

## 📁 專案結構

```
water_bot_project/
├── main.py                  # Bot 主程式進入點
├── constants.py             # 等級配置、身分組 ID 映射
├── database.py              # SQLite 資料庫初始化與管理
├── event_manager.py         # 事件系統（Combo 機制相關）
├── update_db.py             # 資料庫遷移與升級工具
│
├── cogs/                    # Discord.py Cogs（功能模組）
│   ├── water_reminder.py    # 喝水打卡系統、睡眠統計
│   ├── level_system.py      # 等級、排行榜系統
│   ├── admin.py             # 管理員控制面板
│   ├── answer_book.py       # 解答之書
│   ├── fortune.py           # 運勢抽籤
│   ├── daily_news.py        # 每日新聞（AI 整理）
│   └── reaction_roles.py    # 身分組管理（反應綁定、下拉選單）
│
├── water_exp.db             # SQLite 資料庫檔案
├── answers.json             # 解答之書的回答資料庫
├── fortune.json             # 運勢抽籤的結果資料庫
├── events.json              # 事件配置檔
├── water_messages.json      # 喝水提醒訊息範本
│
├── .env                     # Discord Token（需自行創建）
├── groq.env                 # Groq API Key（需自行創建）
├── .gitignore               # Git 忽略清單
└── README.md                # 本檔案
```

---

## 🚀 快速開始

### 前置條件

- **Python 3.8+**（推薦 3.10 或更新）
- **pip** 套件管理工具
- **Discord 伺服器管理員權限**（用於測試機器人）
- **Discord Bot Token**（從 [Discord Developer Portal](https://discord.com/developers/applications) 獲取）
- **Groq API Key**（可選，用於 AI 新聞功能）

### 1️⃣ 複製與環境設定

```bash
# 複製專案
git clone <repository_url>
cd water_bot_project

# 建立虛擬環境（建議）
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# 安裝依賴
pip install -r requirements.txt
```

### 2️⃣ 配置環境變數

在專案根目錄建立 `.env` 檔案：
```env
DISCORD_TOKEN=your_bot_token_here
```

（可選）如需使用新聞功能，建立 `groq.env` 檔案：
```env
GROQ_API_KEY=your_groq_api_key
```

⚠️ **重要**：確保 `.env` 和 `groq.env` 已加入 `.gitignore`，防止金鑰外洩。

### 3️⃣ 設定身分組 ID

有三種方式設定身分組：

#### 方式 A：自動建立（推薦）
機器人會自動建立 30 個身分組：
```
/admin create_roles
```
機器人會下載 `role_mapping.py` 檔案，複製內容到 `constants.py` 中的 `ROLE_MAPPING`。

#### 方式 B：自動掃描（現有身分組）
如果伺服器已有身分組，讓機器人自動掃描匹配：
```
/admin generate_mapping
```
機器人會按稱號名稱自動匹配身分組 ID，並提供 `role_mapping.py` 下載。

#### 方式 C：手動編輯
編輯 `constants.py` 中的 `ROLE_MAPPING` 字典，將每個等級的虛擬 ID 替換為實際身分組 ID：
```python
ROLE_MAPPING = {
    1: 1234567890,  # 非術師・對乾渴無感的凡人
    2: 1234567891,  # 窗・察覺水分流失的徵兆
    # ... 以此類推
}
```

### 4️⃣ 設定通知頻道

編輯 `cogs/water_reminder.py` 和 `cogs/daily_news.py`，設定目標頻道 ID：
```python
target_channel_id = 1234567890  # 替換為你的頻道 ID
```

### 5️⃣ 啟動機器人

```bash
python main.py
```

如果看到以下輸出，表示機器人已成功啟動：
```
資料庫初始化完成
已載入模組: cogs.xxx
已載入模組: cogs.yyy
斜線指令同步完成
Bot 已經成功登入為 YourBotName#0000
```

---

## 📋 使用指令

### 🎮 使用者指令

#### 等級與排名
```
/rank                    查看個人喝水等級與經驗值進度
/leaderboard [page]      查看全伺服器排行榜（支援多頁）
```

#### 娛樂功能
```
/ask_book [問題]         從解答之書中隨機抽取智慧回覆
/fortune                 進行每日運勢占卜
```

#### 其他
```
!test_water             測試喝水提醒（發送一則通知）
```

### 👑 管理員指令

所有管理員指令使用 `/admin` 前綴（需要伺服器管理者權限）：

#### 查詢與統計
```
/admin check <@使用者>       查詢使用者的完整後台數據
```

#### 系統控制
```
/admin trigger_water         立即發送一則喝水通知
/admin toggle_water start    啟動自動喝水排程
/admin toggle_water stop     停止自動喝水排程
```

#### 資料管理
```
/admin backup_db             下載資料庫備份
/admin remove_user <@使用者> ⚠️ 刪除使用者所有遊戲數據
```

#### 身分組設定
```
/admin create_roles          自動建立 30 個身分組
/admin generate_mapping      從現有身分組掃描產生 ROLE_MAPPING
/admin test_welcome          測試新伺服器歡迎訊息
```

#### 下拉選單（身分組面板）
```
/role_ui spawn <標題> <@身分組1> [身分組2~5]
```
例：`/role_ui spawn "選擇你的興趣" @遊戲 @動漫 @音樂`

### 🔗 身分組管理

#### 反應綁定（傳統方式）
```
!roleReact add <訊息ID> <@身分組> <表情符號>
```
例：`!roleReact add 123456789 @Member ❤️`

---

## 🎮 遊戲機制詳解

### 經驗值系統

**打卡獎勵**：
- 基礎獎勵：每次打卡 **10 EXP**
- Combo 獎勵：每 5 Combo 額外 **+5 EXP**（共 15 EXP）

**升級公式**：
```
當前等級所需 EXP = 50 × 當前等級 + 50
```

**進度範例**：
| 升級 | 所需 EXP | 累積 EXP |
|-----|--------|--------|
| Lv.1 → 2 | 100 | 100 |
| Lv.2 → 3 | 150 | 250 |
| Lv.10 → 11 | 600 | 3,350 |
| Lv.20 → 21 | 1,100 | 12,100 |
| Lv.30（最高） | 1,550 | 51,500+ |

### Combo 機制

**延續條件**：
- 系統每 30 分鐘（10:00～23:30）發送一個「回合」
- 若使用者在該回合內打卡，Combo +1
- 若下次打卡的回合是 `上次回合 + 1`，Combo 繼續累計
- 否則 Combo 歸零，重新開始

**獎勵觸發**：
- Combo x5：額外 +5 EXP
- Combo x10：額外 +5 EXP
- Combo x15、x20、... 依此類推

**例子**：
```
Day 1, 10:00 - 打卡 → Combo: 1
Day 1, 10:30 - 打卡 → Combo: 2
Day 1, 11:00 - 打卡 → Combo: 3
Day 1, 11:30 - 打卡 → Combo: 4
Day 1, 12:00 - 打卡 → Combo: 5 ⭐ (+5 EXP 獎勵)
Day 1, 14:00 - 打卡（跳過 3 個回合）→ Combo: 0 (重置)
```

### 身分組同步

**首次打卡**：
- 自動獲得 **Lv.1 身分組**（非術師・對乾渴無感的凡人）

**升級時**：
- 自動移除舊身分組
- 自動新增新身分組
- 身分組顏色與等級對應，視覺化展示進度

### 每日回合機制

| 時間 | 回合 |
|-----|------|
| 10:00 | 第 1 回合 |
| 10:30 | 第 2 回合 |
| 11:00 | 第 3 回合 |
| ... | ... |
| 23:30 | 第 28 回合 |
| 23:30 後 | 無回合（Combo 重置） |

---

## 🗄️ 資料庫結構

### 表格設計

#### `users` - 使用者遊戲數據
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,        -- Discord 使用者 ID
    total_exp INTEGER DEFAULT 0,     -- 總經驗值
    daily_exp INTEGER DEFAULT 0,     -- 今日已獲得 EXP
    combo INTEGER DEFAULT 0,         -- 連續打卡次數
    last_round INTEGER DEFAULT 0,    -- 最後打卡的系統回合數
    wake_time TEXT,                  -- 起床時間（HH:MM 格式）
    sleep_time TEXT                  -- 就寢時間（HH:MM 格式）
)
```

#### `claims` - 打卡防重複紀錄
```sql
CREATE TABLE claims (
    message_id TEXT,                 -- 喝水通知訊息 ID
    user_id TEXT,                    -- 打卡使用者 ID
    PRIMARY KEY(message_id, user_id)
)
```

#### `reaction_roles` - 反應綁定規則
```sql
CREATE TABLE reaction_roles (
    message_id TEXT,                 -- 訊息 ID
    emoji TEXT,                      -- 表情符號
    role_id TEXT,                    -- 身分組 ID
    PRIMARY KEY(message_id, emoji)
)
```

#### `system_state` - 系統狀態變數
```sql
CREATE TABLE system_state (
    key TEXT PRIMARY KEY,            -- 狀態鍵
    value TEXT                       -- 狀態值
)
```

**常見 system_state 鍵**：
- `active_water_message`：目前活躍的喝水通知訊息 ID
- `current_round`：目前系統回合數
- `last_news_time`：最後發送新聞的時間

---

## ⚙️ 配置說明

### constants.py

#### TITLE_DATA
定義每個等級的稱號與顏色：
```python
TITLE_DATA = {
    1: {"title": "非術師・對乾渴無感的凡人", "color": "#bdc3c7"},
    2: {"title": "窗・察覺水分流失的徵兆", "color": "#ecf0f1"},
    # ...
    30: {"title": "詛咒之王・千年不渴的至高宿儺", "color": "#1b2631"}
}
```

#### ROLE_MAPPING
映射等級到 Discord 身分組 ID：
```python
ROLE_MAPPING = {
    1: 1234567890,  # Lv.1 身分組 ID
    2: 1234567891,  # Lv.2 身分組 ID
    # ... 以此類推到 30
}
```

### 其他配置檔案

#### `water_messages.json`
喝水提醒訊息的範本集合。

#### `answers.json`
解答之書的回答資料庫（JSON 格式）。

#### `fortune.json`
運勢占卜的結果資料庫（JSON 格式）。

#### `events.json`
系統事件配置（如喝水排程時間）。

---

## 🔐 安全與權限

### Token 與 API Key 管理

**⚠️ 最佳實踐**：
- ❌ **不要**在代碼中硬編碼 Token 或 API Key
- ✅ **使用** `.env` 檔案隱藏敏感資訊
- ✅ **確保** `.env` 和 `groq.env` 在 `.gitignore` 中
- ✅ **定期**更換 Token（如果外洩）

### Discord 指令權限

| 指令 | 所需權限 | 說明 |
|-----|--------|------|
| `/rank`, `/leaderboard`, `/ask_book`, `/fortune` | 無 | 所有使用者可用 |
| `/role_ui spawn` | 伺服器管理者 | 管理員指令 |
| `/admin *` | 伺服器管理者 | 所有 admin 子指令 |
| `!roleReact add` | 管理身分組 | 身分組管理員 |

### 機器人必需權限

請確保機器人在伺服器中擁有以下權限：
- ✅ 傳送訊息
- ✅ 嵌入連結
- ✅ 管理身分組
- ✅ 建立 Webhook
- ✅ 新增反應
- ✅ 管理訊息

### 敏感操作

| 操作 | 說明 | 警告 |
|-----|------|------|
| `/admin remove_user` | 刪除使用者所有遊戲數據 | ⚠️ **無法復原** |
| `/admin backup_db` | 下載資料庫備份 | 包含所有使用者數據 |
| `ROLE_MAPPING` 設定 | 身分組 ID 映射 | 錯誤設定會導致身分組無法正確發放 |

### Cogs 模組說明

#### water_reminder.py
- 喝水打卡系統的核心
- 每 30 分鐘自動發送提醒（10:00～23:30）
- 管理 Combo 機制與打卡防重複邏輯
- 提供睡眠統計功能

#### level_system.py
- 經驗值與等級計算
- `/rank` 命令實現
- `/leaderboard` 排行榜展示
- 身分組自動同步

#### admin.py
- 所有 `/admin` 指令實現
- 身分組自動建立與掃描
- 資料庫備份功能

#### daily_news.py
- Google News RSS 爬蟲
- Groq AI 新聞整理
- Webhook 動態管理
- 排程控制

#### answer_book.py
- 解答之書的隨機選取邏輯
- JSON 資料庫讀取
- 過場動畫實現

#### fortune.py
- 運勢占卜系統
- 重抽機制與冷卻控制
- 嘲諷語錄系統

#### reaction_roles.py
- 反應綁定的 on_raw_reaction_add 監聽
- 下拉選單的 Select 實現
- 互斥身分組邏輯

### 資料庫初始化

首次運行 `python main.py` 時，`database.py` 會自動建立以下表格。若需要遷移舊版本數據，使用 `update_db.py`：

```bash
python update_db.py
```