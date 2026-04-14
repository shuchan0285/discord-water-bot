# 🥤 Water Reminder Bot - 喝水提醒機器人

一個基於 **Discord.py** 開發的喝水提醒機器人，融合《咒術迴戰》主題設定。透過遊戲化機制鼓勵使用者養成健康的飲水習慣。

---

## ✨ 核心功能

### 1️⃣ **喝水打卡系統** (`water_reminder.py`)
- **定時提醒**：每天 **10:00 ~ 23:30**（每 30 分鐘一次）自動發送喝水通知訊息
- **互動式打卡按鈕**：使用者按下「喝了！🥤」按鈕進行打卡，防止重複領取獎勵
- **Combo 機制**：連續打卡可增加 Combo 倍數，每 5 Combo 觸發額外獎勵（**+5 EXP**）
- **自動身分組發放**：首次打卡時自動獲得 Lv.1 身分組，升級時自動替換為對應身分組
- **過期通知提示**：舊訊息打卡時提醒使用者找最新通知

### 2️⃣ **等級與排行榜系統** (`level_system.py`)
- **等級計算**：公式為 `每級所需 EXP = 50 × 等級 + 50`
- **30 階段系統**：從「非術師」到「詛咒之王」，每個等級對應獨特的咒術迴戰稱號
- **視覺化進度條**：使用區塊字符（■□）顯示升級進度
- **彩色排行榜**：`/leaderboard` 指令查看全伺服器排名，支援分頁、彩色身分組顯示、獎牌符號
- **等級重設**：使用者可主動透過 `/rank` 指令重設自己的等級

### 3️⃣ **身分組系統** - 雙模式設計

#### 模式 A：表情符號綁定 (`reaction_roles.py`)
- **反應綁定**：管理員透過 `!roleReact add` 將訊息上的表情符號綁定身分組
- **互斥切換**：一則訊息上的身分組採取「互斥」邏輯，選擇一個表情自動移除其他
- **資料庫管理**：所有綁定規則永久儲存於 SQLite

#### 模式 B：下拉選單 UI (`role_ui.py`)
- **視覺化介面**：管理員透過 `/role_ui spawn` 建立美觀的下拉選單面板
- **靈活配置**：支援 **1~5 個選項**，每個對應一個身分組
- **互斥邏輯**：選擇一個身分組自動移除該選單的其他身分組
- **取消功能**：使用者可清空選單來「卸下」該面板的身分組

### 4️⃣ **管理員控制面板** (`admin.py`)
- **查看使用者數據**：`/admin check <使用者>` - 查詢後台 EXP、Combo、最後打卡回合
- **手動觸發通知**：`/admin trigger_water` - 立即發送一則喝水通知
- **排程控制**：`/admin toggle_water [start|stop]` - 啟動/停止自動喝水排程
- **資料庫備份**：`/admin backup_db` - 下載目前的資料庫檔案備份
- **移除使用者**：`/admin remove_user <使用者>` - 徹底刪除所有遊戲數據
- **仙人歡迎訊息**：`/admin test_welcome` - 手動測試新伺服器歡迎訊息
- **自動建立身分組**：`/admin create_roles` - 一鍵建立 30 個稱號身分組並產生 `ROLE_MAPPING`
- **生成 Mapping 程式碼**：`/admin generate_mapping` - 從現有身分組掃描並產生 `ROLE_MAPPING` 配置

### 5️⃣ **每日新聞模組** (`daily_news.py`)
- **自動早報**：每日早上 **8:00**（台灣時間）發送一次新聞摘要
- **Groq AI 整理**：使用 **Llama 3.3 70B** 模型為新聞撰寫深入摘要（~100 字）
- **RSS 爬蟲**：自動抓取 Google News 台灣新聞（前 3 則）
- **智能網址縮短**：使用 `is.gd` 服務自動縮短新聞連結
- **動態 Webhook**：自動建立或查找「貓咪早報」Webhook，以貓咪名義發送訊息
- **測試指令**：輸入 `!test_news` 立即測試早報功能（測試完自動刪除指令）
- **友善的角色設定**：以「可愛貓咪」身份撰寫摘要，語氣親切活潑

### 6️⃣ **解答之書模組** (`answer_book.py`)
- **互動式抽籤**：使用 `/ask_book` 指令從海量解答中隨機抽取智慧回覆
- **多語言支持**：內建繁體中文與英文雙語回答
- **情感分析**：根據 JSON 標籤自動調整回答語氣（neutral、wisdom、humor、ominous 等）
- **過場動畫**：仙人翻書與思考的互動式視覺效果
- **彈性提問**：支援有具體問題或在心中默念兩種模式
- **JSON 資料庫**：所有答案儲存在 `answers.json` 中，易於擴充

### 7️⃣ **幸運抽籤模組** (`fortune.py`)
- **運勢占卜**：使用 `/fortune` 指令進行每日運勢抽籤
- **吉凶等級**：支援 大吉、中吉、小吉、平、小凶、中凶、大凶 七個等級
- **仙人互動**：「摸魚仙人」以詼諧風趣的語調引導抽籤過程
- **重抽機制**：使用者可點擊「重抽」按鈕，仙人會給出隨機嘲諷語錄（限時 10 分鐘）
- **彩色嵌入訊息**：根據運勢等級自動調整訊息色彩
- **個人化運勢**：針對愛情、財運、學業、工作等不同面向提供建議
- **JSON 資料庫**：抽籤結果儲存在 `fortune.json` 中

---

## 📊 等級與稱號系統

機器人設計了 **30 個等級**，每個等級對應獨特的咒術迴戰主題稱號與顏色：

| 等級 | 稱號 | 顏色代碼 |
|------|------|--------|
| Lv.1 | 非術師・對乾渴無感的凡人 | #bdc3c7 (灰) |
| Lv.5 | 三級術師・瓶裝水的支配者 | #82e0aa (綠) |
| Lv.10 | 準一級術師・邁向水的彼端 | #1d8348 (深綠) |
| Lv.15 | 咒胎・體內水分的二次進化 | #e67e22 (橙) |
| Lv.20 | 反轉術式・瞬間修復乾裂 | #ffffff (白) |
| Lv.30 | 詛咒之王・千年不渴的至高宿儺 | #1b2631 (黑) |

> 完整列表請見 `constants.py` 中的 `TITLE_DATA` 字典

---

## 🗄️ 資料庫結構

### SQLite 表格設計

#### 1. **users**
存儲使用者的遊戲進度數據：
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,        -- Discord 使用者 ID
    total_exp INTEGER DEFAULT 0,     -- 總經驗值
    combo INTEGER DEFAULT 0,         -- 連續打卡次數
    last_round INTEGER DEFAULT 0     -- 最後打卡的系統回合數
)
```

#### 2. **claims**
防止重複領取獎勵：
```sql
CREATE TABLE claims (
    message_id TEXT,       -- 喝水通知訊息 ID
    user_id TEXT,         -- 打卡使用者 ID
    PRIMARY KEY(message_id, user_id)
)
```

#### 3. **reaction_roles**
儲存身分組綁定規則：
```sql
CREATE TABLE reaction_roles (
    message_id TEXT,      -- 訊息 ID
    emoji TEXT,           -- 表情符號
    role_id TEXT,         -- 身分組 ID
    PRIMARY KEY(message_id, emoji)
)
```

#### 4. **system_state**
儲存系統狀態變數：
```sql
CREATE TABLE system_state (
    key TEXT PRIMARY KEY,  -- 狀態鍵（如 'active_water_message', 'current_round'）
    value TEXT            -- 狀態值
)
```

---

## 🚀 快速開始

### 前置條件
- **Python 3.8+**
- **discord.py 2.0+** 或更新版本
- **Groq API 金鑰**（用於 AI 新聞整理）
- **aiohttp**（非同步 HTTP 請求）
- **BeautifulSoup4**（HTML 解析）

### 安裝步驟

1. **複製專案**
   ```bash
   git clone <repository_url>
   cd water_bot_project
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

3. **環境設定**
   - 創建 `.env` 檔案（同級於 `main.py`）：
     ```env
     DISCORD_TOKEN=your_bot_token_here
     ```
   - 創建 `groq.env` 檔案（用於 AI 新聞功能）：
     ```env
     GROQ_API_KEY=your_groq_api_key
     ```

4. **設定身分組 ID**
   - **方式 1：使用管理員指令自動建立**
     ```
     /admin create_roles
     ```
     機器人會自動建立 30 個身分組，並提供 `ROLE_MAPPING` 程式碼供複製

   - **方式 2：從現有身分組掃描**
     ```
     /admin generate_mapping
     ```
     機器人會掃描伺服器現有的身分組，自動匹配稱號名稱

   - **方式 3：手動編輯**
     編輯 `constants.py` 中的 `ROLE_MAPPING` 字典，將虛擬 ID 替換為實際身分組 ID

5. **設定新聞頻道與功能**
   - 編輯 `cogs/water_reminder.py` 中的 `target_channel_id` 為你的喝水通知頻道
   - 編輯 `cogs/daily_news.py` 中的 `target_channel_id` 為你的新聞發送頻道

6. **啟動機器人**
   ```bash
   python main.py
   ```

---

## 📋 使用者指令

### 斜線指令 (`/`)

#### 等級與排名
- **`/rank`** - 查看個人喝水等級、經驗值進度
  - 顯示目前等級、當前進度條、距離下一級所需 EXP

- **`/leaderboard [page]`** - 查看全伺服器排行榜
  - 顯示排名、使用者名稱、總 EXP、當前等級
  - 預設每頁 10 人，支援多頁查詢
  - 前三名顯示獎牌符號（🥇🥈🥉）

#### 娛樂與占卜功能
- **`/ask_book [問題]`** - 召喚摸魚仙人翻開《解答之書》
  - 隨機抽取一條智慧回答（繁體中文與英文雙語）
  - 支援有具體問題或在心中默念兩種模式
  - 回答會根據設定的語氣呈現不同風格

- **`/fortune`** - 進行每日運勢抽籤
  - 摸魚仙人為你占卜運勢
  - 顯示吉凶等級（大吉 ~ 大凶）及運勢詳解
  - 支援重抽功能，仙人會給出不同的嘲諷語錄

#### 身分組管理 (管理員)
- **`/role_ui spawn <標題> <@身分組1> [身分組2~5]`** - 建立下拉選單身分組面板
  - 支援 1~5 個選項，使用者可彈性選擇
  - 例：`/role_ui spawn "選擇你的興趣" @遊戲 @動漫 @音樂`

### 普通指令 (`!`)

#### 身分組管理（管理員專用）
- **`!roleReact add <訊息ID> <@身分組> <表情符號>`**
  - 將指定訊息的表情符號綁定身分組
  - 例：`!roleReact add 123456 @Member ❤️`

#### 測試指令
- **`!test_news`** - 立即觸發新聞早報（測試用）
  - 發送後自動刪除指令訊息
- **`!test_water`** - 立即發送喝水通知（測試用）

---

## 🔧 管理員指令詳解

### `/admin` 指令群組

#### 查詢與數據管理
```
/admin check <使用者>
```
查詢使用者的完整後台數據（EXP、等級、Combo、最後回合）

#### 系統控制
```
/admin trigger_water
```
立即發送一則喝水通知（用於臨時提醒）

```
/admin toggle_water [start|stop]
```
- `start`：啟動自動喝水排程
- `stop`：停止自動喝水排程

#### 資料管理
```
/admin backup_db
```
下載資料庫備份檔案（`.db` 格式）

```
/admin remove_user <使用者>
```
⚠️ **危險指令**：完全刪除使用者的所有遊戲數據（無法復原）

#### 身分組與伺服器設定
```
/admin create_roles
```
自動批次建立 30 個稱號身分組並產生 Python 程式碼
- 建立完成後下載 `role_mapping.py`
- 將內容複製到 `constants.py` 中的 `ROLE_MAPPING`

```
/admin generate_mapping
```
從伺服器現有身分組掃描，自動產生 `ROLE_MAPPING` 程式碼
- 按稱號名稱自動匹配身分組 ID
- 提供 `role_mapping.py` 檔案供下載

```
/admin test_welcome
```
手動測試「仙人歡迎訊息」（新成員加入時的歡迎說明）

---

## 🎮 遊戲機制詳解

### 經驗值與等級

**打卡獎勵**：
- 每次打卡獲得 **10 EXP**（基礎）
- 每 5 Combo 額外獎勵 **+5 EXP**（合計 15 EXP）

**升級公式**：
```
當前等級所需 EXP = 50 × 當前等級 + 50
```

例：
- Lv.1 → Lv.2：需 100 EXP
- Lv.2 → Lv.3：需 150 EXP
- Lv.10 → Lv.11：需 600 EXP
- Lv.30：需累積超過 51,500 EXP

### Combo 機制

**延續條件**：
- 若當前「系統回合」= 上次打卡回合 + 1，Combo 繼續累計
- 否則 Combo 歸零，重新開始計數

**獎勵觸發**：
- 每 5 Combo 觸發一次額外獎勵
- Combo x5, x10, x15, ... 時各獲得 +5 EXP

**每日機制**：
- 系統每 30 分鐘（10:00 ~ 23:30）發送一則「回合」
- 使用者在該回合內打卡一次，Combo +1
- 錯過該回合，下次打卡時 Combo 歸零

### 身分組同步

**首次打卡**：
- 獲得 Lv.1 身分組（自動發放）

**升級時**：
- 自動移除舊身分組（前一個等級）
- 自動新增新身分組（新等級）
- 支援自訂顏色，視覺化等級進度

---

## 🔐 安全與權限

### Token 與金鑰管理
- **務必不要**在代碼中硬編碼 Token 或 API Key
- 使用 `.env` 和 `groq.env` 檔案隱藏敏感資訊
- 將 `.env` 和 `groq.env` 加入 `.gitignore` 防止上傳

### 指令權限
- **管理員指令** (`/admin`, `/role_ui`) 需要「**管理者**」權限
- **身分組管理** (`!roleReact`) 需要「**管理身分組**」權限
- **普通使用者**可執行 `/rank`、`/leaderboard` 等查詢指令

### 機器人權限檢查清單
機器人需要以下 Discord 權限：
- ✅ 傳送訊息
- ✅ 嵌入連結
- ✅ 管理身分組
- ✅ 建立 Webhook
- ✅ 新增反應
- ✅ 管理訊息

---

## 🐛 常見問題

### Q: 機器人無法啟動？
**A**: 檢查以下項目：
1. `.env` 檔案是否存在並包含有效的 `DISCORD_TOKEN`
2. Token 是否正確（未被複製錯誤）
3. 機器人是否已邀請至伺服器
4. 機器人是否有必要的權限（傳送訊息、管理身分組等）
5. 檢查控制台是否有 Python 錯誤訊息

### Q: 喝水通知沒有按時發送？
**A**:
1. 檢查 `cogs/water_reminder.py` 中的 `target_channel_id` 是否正確
2. 確認機器人對該頻道有「傳送訊息」權限
3. 使用 `/admin trigger_water` 手動測試
4. 檢查 `/admin toggle_water` 排程是否已啟動

### Q: 打卡後沒有獲得身分組？
**A**: 
1. 檢查 `constants.py` 中的 `ROLE_MAPPING` 是否設定正確
2. 確認身分組 ID 確實存在於伺服器
3. 檢查機器人身分組是否排列在目標身分組之上（Discord 設定）
4. 嘗試使用 `/admin generate_mapping` 自動掃描並重新生成 Mapping

### Q: Combo 為什麼歸零了？
**A**: 
- 系統追蹤最後打卡的「回合數」
- 若中間間隔 ≥ 1 個回合，Combo 會歸零
- 系統每 30 分鐘重置一個回合
- 例：10:00 打卡 (Combo x1) → 10:30 未打 → 11:00 才打 (Combo 歸零，重新開始)

### Q: 新聞模組無法運行？
**A**:
1. 檢查 `groq.env` 是否包含有效的 `GROQ_API_KEY`
2. 檢查 `cogs/daily_news.py` 中的 `target_channel_id` 是否正確
3. 使用 `!test_news` 指令手動測試
4. 檢查網路連線是否正常（需要存取 Google News RSS）

### Q: 解答之書無法顯示答案？
**A**:
1. 檢查 `answers.json` 檔案是否存在並包含有效 JSON 資料
2. 確認 JSON 結構正確（必需包含 `answer` 和 `meta` 欄位）
3. 檢查控制台中的載入訊息，確認有成功讀取答案資料
4. 若檔案損毀，重新建立 `answers.json` 並補充答案資料

### Q: 抽籤顯示為空？
**A**:
1. 檢查 `fortune.json` 檔案是否存在且包含抽籤資料
2. 確認 JSON 結構正確（必需包含 `fortune_results` 陣列）
3. 檢查機器人控制台的日誌，查看是否有載入錯誤
4. 確保 `fortune.json` 使用 UTF-8 編碼

### Q: 如何自訂解答之書的答案？
**A**:
編輯 `answers.json` 檔案，按以下格式新增或修改答案：
```json
{
  "answer_1": {
    "answer": {
      "zh-TW": "你的繁體中文答案",
      "en": "Your English answer"
    },
    "meta": {
      "tone": "wisdom",
      "category": "life"
    }
  }
}
```
支援的語氣類型（tone）：neutral、wisdom、humor、ominous、mysterious 等。

### Q: 如何自訂抽籤的運勢類型？
**A**:
編輯 `fortune.json` 檔案中的 `fortune_results` 陣列，按格式新增運勢資料：
```json
{
  "fortune_results": [
    {
      "level": "大吉",
      "color": "#ff0000",
      "description": "運勢描述",
      "love": "愛情建議",
      "wealth": "財運建議",
      "study": "學業建議",
      "work": "工作建議"
    }
  ]
}
```

### Q: 如何重置某使用者的數據？
**A**: 
使用管理員指令：
```
/admin remove_user @使用者
```
此指令會徹底刪除該使用者的所有紀錄（無法復原）。

### Q: 如何自訂喝水提醒時間？
**A**:
編輯 `cogs/water_reminder.py` 中的 `trigger_times` 設定：
```python
trigger_times = []
for h in range(10, 24):  # 改成你想要的時段
    trigger_times.append(datetime.time(hour=h, minute=0, tzinfo=tz))
    trigger_times.append(datetime.time(hour=h, minute=30, tzinfo=tz))
```

---

## 🛠️ 開發與擴展

### 修改通知時間
編輯 `cogs/water_reminder.py` 中的時間設定：

```python
# 目前：10:00 ~ 23:30，每 30 分鐘一次
trigger_times = []
for h in range(10, 24):  # 改成 range(9, 23) 變成 9:00 ~ 22:30
    trigger_times.append(datetime.time(hour=h, minute=0, tzinfo=tz))
    trigger_times.append(datetime.time(hour=h, minute=30, tzinfo=tz))
```

### 修改新聞發送時間
編輯 `cogs/daily_news.py` 中的排程：

```python
# 目前：每天早上 8:00
trigger_time = datetime.time(hour=8, minute=0, tzinfo=tz)
# 改成早上 7:00：
# trigger_time = datetime.time(hour=7, minute=0, tzinfo=tz)
```

### 自訂稱號與顏色
編輯 `constants.py` 中的 `TITLE_DATA` 字典：

```python
TITLE_DATA = {
    1: {"title": "你的稱號", "color": "#十六進制顏色"},
    2: {"title": "另一個稱號", "color": "#ff0000"},
    # ...
}
```

### 調整經驗值計算
修改 `database.py` 中的 `claim_exp()` 函數：

```python
# 修改基礎獲得經驗值（目前 10）
new_total = old_total + 10 + bonus_exp  # 改成 20 就是每次 20 EXP

# 修改 Combo 獎勵（目前每 5 Combo +5 EXP）
if (new_combo > 0 and new_combo % 5 == 0):  # 改成 % 10 變成每 10 Combo 一次
    bonus_exp = 5  # 改成其他數值
```

---

## 📚 技術棧

- **Python 3.8+**
- **discord.py 2.0+** - Discord Bot 框架
- **SQLite** - 輕量級資料庫
- **aiohttp** - 非同步 HTTP 請求
- **BeautifulSoup4** - HTML 解析與 RSS 爬蟲
- **Groq API** - AI 模型（Llama 3.3 70B，用於新聞摘要）
- **python-dotenv** - 環境變數管理
- **feedparser** - RSS 訂閱源解析
- **requests** - HTTP 請求庫（URL 縮短服務）

## 📁 專案結構

```
water_bot_project/
├── main.py                    # 機器人主程式進入點
├── database.py                # 資料庫初始化與操作函數
├── constants.py               # 設定檔（等級稱號、身分組對應）
├── update_db.py               # 資料庫升級腳本
├── answers.json               # 解答之書答案資料庫
├── fortune.json               # 抽籤運勢資料庫
├── .env                       # Discord Token（需自行建立）
├── groq.env                   # Groq API Key（需自行建立）
└── cogs/                      # 功能模組資料夾
    ├── __init__.py
    ├── water_reminder.py      # 喝水打卡與通知模組
    ├── level_system.py        # 等級與排行榜系統
    ├── admin.py               # 管理員控制面板
    ├── reaction_roles.py      # 表情符號身分組綁定
    ├── role_ui.py             # 下拉選單身分組 UI
    ├── daily_news.py          # 每日新聞早報模組
    ├── answer_book.py         # 解答之書互動模組
    └── fortune.py             # 幸運抽籤模組
```

---

## 🎉 致謝

感謝所有使用者的支持與反饋！

祝你水喝得開心！🥤✨
