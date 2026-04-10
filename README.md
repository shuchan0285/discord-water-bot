# 🥤 Water Reminder Bot - 喝水提醒機器人

一個基於 **Discord.py** 開發的喝水提醒機器人，融合《咒術迴戰》主題設定。透過遊戲化機制鼓勵使用者養成健康的飲水習慣。

---

## ✨ 核心功能

### 1️⃣ **喝水打卡系統** (`water_reminder.py`)
- **定時提醒**：每隔固定時間發送一則喝水通知訊息（帶有打卡按鈕）
- **一次性打卡**：使用者按下「喝了！🥤」按鈕進行打卡，防止重複領取獎勵
- **Combo 機制**：連續打卡可增加 Combo 倍數，每 5 Combo 觸發額外獎勵（+5 EXP）
- **升級系統**：累積經驗值（EXP）升級，獲得階級稱號與身分組

### 2️⃣ **等級與排行榜系統** (`level_system.py`)
- **等級計算**：公式為 `每級所需 EXP = 50 × 等級 + 50`
- **30 階段系統**：從「非術師」到「詛咒之王」，每個等級對應獨特的咒術迴戰稱號
- **視覺化進度條**：使用區塊字符顯示升級進度
- **排行榜查詢**：`/leaderboard` 指令查看全伺服器排名（支援分頁）

### 3️⃣ **身分組系統** (`reaction_roles.py`)
- **反應綁定**：管理員可透過 `!roleReact add` 將訊息上的表情符號綁定身分組
- **互斥切換**：一則訊息上的身分組採取「互斥」邏輯，使用者選擇一個表情會自動移除其他身分組
- **資料庫管理**：所有綁定規則永久儲存於 SQLite 資料庫

### 4️⃣ **管理員控制面板** (`admin.py`)
- **查看使用者數據**：`/admin check <使用者>` - 查詢後台 EXP、Combo、最後打卡回合等詳細資訊
- **經驗值調整**：`/admin modify_exp <使用者> <數值> [add|set]` - 增減或強制設定經驗值
- **移除使用者**：`/admin remove_user <使用者>` - 徹底刪除使用者的所有遊戲數據
- **手動觸發通知**：`/admin trigger_water` - 立即發送一則喝水通知（用於測試）

### 5️⃣ **每日新聞模組** (`daily_news.py`)
- 支援定時發送每日新聞或資訊推送
- 可自訂內容與發送時間

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
- **Groq API 金鑰**（若使用 AI 功能）

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
   - 創建 `groq.env` 檔案（若使用 AI 功能）：
     ```env
     GROQ_API_KEY=your_groq_api_key
     ```

4. **設定身分組 ID**
   - 編輯 `constants.py` 中的 `ROLE_MAPPING` 字典
   - 將虛擬 ID 替換為你 Discord 伺服器中的實際身分組 ID
   - 確保每個等級都對應正確的身分組

5. **啟動機器人**
   ```bash
   python main.py
   ```

---

## 📋 使用者指令

### 斜線指令 (`/`)

#### 等級與排名
- **`/rank`** - 查看個人喝水等級、經驗值進度與排名
  - 顯示目前等級、當前進度條、距離下一級所需 EXP
  - 提供「重設等級」按鈕（謹慎使用，重設後無法恢復）

- **`/leaderboard [page]`** - 查看全伺服器排行榜
  - 顯示排名、使用者名稱、總 EXP、當前等級
  - 預設每頁 10 人，支援多頁查詢

### 普通指令 (`!`)

#### 身分組管理（管理員專用）
- **`!roleReact add <訊息ID> <@身分組> <表情符號>`**
  - 將指定訊息的表情符號綁定身分組
  - 例：`!roleReact add 123456 @Member ❤️`

---

## 🔧 管理員指令

### 斜線指令群組 `/admin`

#### 查詢與管理
- **`/admin check <使用者>`**
  - 檢視使用者後台完整數據（EXP、等級、Combo、最後打卡回合）

- **`/admin modify_exp <使用者> <數值> [add|set]`**
  - `add` 模式：增加或減少經驗值（支援負數）
  - `set` 模式：強制設定為指定數值

- **`/admin remove_user <使用者>`**
  - 完全刪除使用者的所有遊戲數據（包含打卡紀錄）
  - ⚠️ 此操作無法復原

#### 系統控制
- **`/admin trigger_water`**
  - 立即發送一則喝水通知
  - 用於測試或臨時提醒

---

## 📁 專案結構

```
water_bot_project/
├── main.py                 # 機器人主程式
├── constants.py            # 等級稱號與身分組 ID 配置
├── database.py             # SQLite 資料庫管理邏輯
├── .env                    # Discord Token（敏感資訊）
├── groq.env                # Groq API Key（若使用 AI）
├── water_exp.db            # SQLite 資料庫檔案
├── cogs/                   # Discord.py Cogs 模組
│   ├── __init__.py
│   ├── water_reminder.py   # 喝水打卡與通知系統
│   ├── level_system.py     # 等級與排行榜
│   ├── reaction_roles.py   # 身分組反應綁定
│   ├── admin.py            # 管理員控制面板
│   └── daily_news.py       # 每日新聞推送
└── __pycache__/            # Python 快取

```

---

## 🎮 遊戲機制詳解

### 經驗值與等級

每次打卡獲得 **10 EXP**。

**Combo 獎勵機制**：
- 每 5 Combo 連續打卡觸發一次額外獎勵，補充 **+5 EXP**
- 若斷卡（未在連續打卡回合內打卡），Combo 歸零重新開始
- 系統追蹤最後打卡的「回合數」，若當前回合 = 上次回合 + 1，則 Combo 繼續累計

**升級公式**：
```
當前等級所需 EXP = 50 × 當前等級 + 50
```
例：
- Lv.1 → Lv.2：需 100 EXP
- Lv.2 → Lv.3：需 150 EXP
- Lv.10 → Lv.11：需 600 EXP

### 身分組同步

當使用者升級時，機器人會自動：
1. 移除舊的身分組（前一個等級的身分組）
2. 新增新的身分組（新等級的身分組）
3. 更新使用者的暱稱或狀態（可選）

### 系統回合

每當發送一則新的喝水通知訊息，`current_round` 計數器 **+1**。
- 用於判斷 Combo 是否延續
- 每個回合只能打一次卡（同一則訊息 + 同一使用者）

---

## 🔐 安全與權限

### Token 管理
- **務必不要**在代碼中硬編碼 Token
- 使用 `.env` 檔案隱藏敏感資訊
- 將 `.env` 加入 `.gitignore` 防止上傳

### 指令權限
- 管理員指令 (`/admin`) 需要伺服器管理員權限
- 身分組相關指令需要「管理身分組」權限
- 普通使用者無法執行修改他人等級等操作

---

## 🐛 常見問題

### Q: 機器人無法啟動？
**A**: 檢查以下項目：
1. `.env` 檔案是否存在並包含有效的 `DISCORD_TOKEN`
2. Token 是否正確（未被複製錯誤）
3. 機器人是否已邀請至伺服器
4. 機器人是否有必要的權限（傳送訊息、管理身分組等）

### Q: 打卡後沒有獲得身分組？
**A**: 
1. 檢查 `constants.py` 中的 `ROLE_MAPPING` 是否設定正確
2. 確認身分組 ID 確實存在於伺服器
3. 檢查機器人身分組是否排列在目標身分組之上

### Q: Combo 為什麼歸零了？
**A**: 
- 若超過一個通知週期未打卡，Combo 會自動歸零
- 系統會檢查最後打卡回合是否連續
- 若中間間隔 ≥ 1 個回合，則 Combo 重新計算

### Q: 如何重置某使用者的數據？
**A**: 
使用管理員指令：
```
/admin remove_user @使用者
```
此指令會徹底刪除該使用者的所有紀錄。

---

## 🛠️ 開發與擴展

### 修改通知時間
編輯 `cogs/water_reminder.py` 中的 `@tasks.loop()` 裝飾器：
```python
@tasks.loop(hours=1)  # 每 1 小時發送一次
async def water_task(self):
    # ...
```

### 自訂稱號與顏色
編輯 `constants.py` 中的 `TITLE_DATA` 字典：
```python
TITLE_DATA = {
    1: {"title": "你的稱號", "color": "#十六進制顏色"},
    # ...
}
```

### 調整經驗值計算
修改 `database.py` 中的 `claim_exp()` 函數：
```python
# 修改獲得的基礎 EXP 數值
new_total = old_total + 10 + bonus_exp  # 改成你想要的數值
```

---

## 📚 技術棧

- **Python 3.8+**
- **discord.py 2.0+** - Discord Bot 框架
- **SQLite** - 輕量級資料庫
- **Groq API**（可選）- AI 功能支援

---

## 🎉 致謝

感謝所有使用者的支持與反饋！
祝你水喝得開心！🥤✨
