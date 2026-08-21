import sqlite3
import datetime

DB_NAME = "water_exp.db"

# ==========================================
# 系統初始化與輔助功能
# ==========================================

def init_db():
    """初始化資料庫表單，並確保後續新增欄位時不會報錯"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, total_exp INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS claims (message_id TEXT, user_id TEXT, PRIMARY KEY(message_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS reaction_roles (message_id TEXT, emoji TEXT, role_id TEXT, PRIMARY KEY(message_id, emoji))''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_state (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_events (user_id TEXT, event_name TEXT, exp_change INTEGER, timestamp TEXT)''')

    columns_to_add = [
        "combo INTEGER DEFAULT 0",
        "last_round INTEGER DEFAULT 0",
        "last_claim_date TEXT",
        "daily_exp INTEGER DEFAULT 0",
        "daily_fortune TEXT DEFAULT ''"
    ]
    for col in columns_to_add:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

def get_logical_date() -> str:
    """邏輯換日：判斷當前時間，清晨 4 點前視為同一天"""
    now = datetime.datetime.now()
    if now.hour < 4:
        return (now - datetime.timedelta(days=1)).date().isoformat()
    return now.date().isoformat()

# ==========================================
# 核心經驗與等級系統
# ==========================================

def get_level_info(total_exp: int):
    """計算等級與升級所需經驗 (方案 B: 二次方成長曲線)"""
    level = 1
    current_exp = total_exp
    while True:
        req_exp = 15 * (level ** 2) + 50 * level + 50
        if current_exp >= req_exp:
            current_exp -= req_exp
            level += 1
        else:
            return level, current_exp, req_exp

def claim_exp(message_id: int, user_id: int, event_exp: int = 0, event_text: str = "") -> tuple:
    """喝水打卡核心邏輯：判定連擊、給予經驗值、記錄隨機機緣明細"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT 1 FROM claims WHERE message_id = ? AND user_id = ?", (str(message_id), str(user_id)))
    if c.fetchone():
        conn.close()
        return False, 0, 0, 0, 0, False

    today_str = get_logical_date()
    yesterday_str = (datetime.datetime.strptime(today_str, "%Y-%m-%d") - datetime.timedelta(days=1)).date().isoformat()
    now_full_time = datetime.datetime.now().strftime("%H:%M:%S")

    def record_detail(u_id, name, val):
        if val != 0:
            c.execute("INSERT INTO daily_events (user_id, event_name, exp_change, timestamp) VALUES (?, ?, ?, ?)",
                      (str(u_id), name, val, now_full_time))

    c.execute("SELECT total_exp, combo, last_round, last_claim_date FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()

    is_first_of_day = False
    current_round = get_current_round()

    record_detail(user_id, "基礎修為", 10)
    if event_exp != 0:
        record_detail(user_id, event_text, event_exp)

    if result:
        old_total, old_combo, last_round, last_claim_date = result

        # Combo 判定
        if last_claim_date == today_str:
            new_combo = old_combo + 1
        elif last_claim_date == yesterday_str:
            new_combo = old_combo + 1
            is_first_of_day = True
        else:
            new_combo = 1
            is_first_of_day = True

        bonus_exp = 5 if (new_combo > 0 and new_combo % 5 == 0) else 0
        if bonus_exp > 0:
            record_detail(user_id, f"連擊獎勵 (Combo x{new_combo})", bonus_exp)

        gain_amount = 10 + bonus_exp + event_exp
        new_total = max(0, old_total + gain_amount)

        c.execute("""
            UPDATE users SET total_exp = ?, combo = ?, last_round = ?, last_claim_date = ?,
            daily_exp = max(0, daily_exp + ?) WHERE user_id = ?
        """, (new_total, new_combo, current_round, today_str, gain_amount, str(user_id)))
    else:
        # 新玩家初始化
        old_total = 0
        bonus_exp = 0
        new_total = 10 + event_exp
        new_combo = 1
        is_first_of_day = True
        c.execute("""
            INSERT INTO users (user_id, total_exp, combo, last_round, last_claim_date, daily_exp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(user_id), new_total, new_combo, current_round, today_str, new_total))

    c.execute("INSERT INTO claims (message_id, user_id) VALUES (?, ?)", (str(message_id), str(user_id)))
    conn.commit()
    conn.close()
    return True, old_total, new_total, new_combo, bonus_exp, is_first_of_day

def get_user_total_exp(user_id: int) -> int:
    """單純查詢使用者的總經驗值 (供 /rank 指令使用)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ==========================================
# 今日明細與運勢系統
# ==========================================

def get_today_events(user_id: int):
    """取得使用者今日的經驗變動明細"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT event_name, exp_change FROM daily_events WHERE user_id = ? ORDER BY timestamp DESC", (str(user_id),))
    results = c.fetchall()
    conn.close()
    return results

def reset_daily_exp():
    """每日結算後，清空所有人的今日經驗與事件明細"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET daily_exp = 0")
    c.execute("DELETE FROM daily_events")
    conn.commit()
    conn.close()

def reset_user_daily_status(user_id: int):
    """將指定使用者的最後打卡日期清空，使其能再次觸發『今日首次抽籤』"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET last_claim_date = '' WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

def set_user_daily_fortune(user_id: int, fortune_type: str):
    """將今日抽籤結果或化解狀態存入資料庫"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET daily_fortune = ? WHERE user_id = ?", (fortune_type, str(user_id)))
    conn.commit()
    conn.close()

def get_user_daily_fortune(user_id: int) -> str:
    """讀取使用者的今日運勢 Buff (跨日則失效回傳空值)"""
    today_str = get_logical_date()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT daily_fortune, last_claim_date FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()

    if result:
        fortune, last_date = result
        if last_date == today_str:
            return fortune if fortune else ""
    return ""

# ==========================================
# 系統排程與通知狀態
# ==========================================

def set_setting(key: str, value: str):
    """通用系統狀態寫入功能"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key: str, default=None):
    """通用系統狀態讀取功能"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default

def set_active_water_message(message_id: int):
    """更新最新的喝水通知 ID，並推進全局回合數"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES ('active_water_message', ?)", (str(message_id),))

    c.execute("SELECT value FROM system_state WHERE key = 'current_round'")
    result = c.fetchone()
    current_round = int(result[0]) if result else 0
    current_round += 1
    c.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES ('current_round', ?)", (str(current_round),))

    conn.commit()
    conn.close()

def get_active_water_message() -> str:
    """取得當前有效的喝水通知 ID，避免使用者點擊舊按鈕"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = 'active_water_message'")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_current_round() -> int:
    """取得當前系統總回合數"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = 'current_round'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 0

def check_last_message_claimed() -> bool:
    """檢查最後發出的喝水通知是否有任何人點擊"""
    active_id = get_active_water_message()
    if not active_id: return True
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM claims WHERE message_id = ?", (str(active_id),))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def increment_missed_rounds():
    """增加連續無人打卡的回合數 (用於深夜提早結束判定)"""
    val = int(get_setting("consecutive_missed", 0))
    set_setting("consecutive_missed", val + 1)

def reset_missed_rounds():
    """重置連續無人打卡的回合數"""
    set_setting("consecutive_missed", 0)

# ==========================================
# 玩家後台數據與排行榜
# ==========================================

def modify_user_exp(user_id: int, exp_amount: int, mode: str = "add") -> tuple:
    """管理員工具：增減 (add) 或強制設定 (set) 玩家經驗值"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    current_exp = result[0] if result else 0

    new_exp = exp_amount if mode == "set" else current_exp + exp_amount
    new_exp = max(0, new_exp) # 防止負數

    if result:
        c.execute("UPDATE users SET total_exp = ? WHERE user_id = ?", (new_exp, str(user_id)))
    else:
        c.execute("INSERT INTO users (user_id, total_exp, combo, last_round) VALUES (?, ?, 0, 0)",
                  (str(user_id), new_exp))

    conn.commit()
    conn.close()
    return current_exp, new_exp

def get_user_full_data(user_id: int):
    """取得玩家完整後台數據 (供 /admin check 使用)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp, combo, last_round FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()
    return result

def remove_user_data(user_id: int):
    """徹底刪除玩家的所有註冊資料與打卡紀錄"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (str(user_id),))
    c.execute("DELETE FROM claims WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

def reset_user_exp(user_id: int):
    """強制將玩家的經驗值、連擊與回合數歸零 (不刪除帳號)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET total_exp = 0, combo = 0, last_round = 0 WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

def get_total_participants_count() -> int:
    """取得伺服器參與修煉的總人數 (供排行榜計算總頁數)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_participants_paged(limit: int, offset: int):
    """依據分頁設定取得參與名單 (按總經驗值降冪排序)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, total_exp FROM users ORDER BY total_exp DESC LIMIT ? OFFSET ?", (limit, offset))
    results = c.fetchall()
    conn.close()
    return results

def get_daily_top_gainer():
    """取得今日進步最快(單日經驗值最高)的玩家"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, daily_exp FROM users WHERE daily_exp > 0 ORDER BY daily_exp DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result

def get_user_today_summary(user_id: int):
    """取得玩家今日總結概況 (經驗總和、連擊、今日獲得)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp, combo, daily_exp, last_claim_date FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()
    return result