import sqlite3

DB_NAME = "water_exp.db"

# ==========================================
# 系統初始化
# ==========================================
def init_db():
    """
    初始化資料庫。在機器人啟動時執行，確保所有需要的資料表都存在。
    - users: 儲存使用者的總經驗值 (EXP)。
    - claims: 儲存喝水打卡紀錄，防止同一則通知重複按。
    - reaction_roles: 儲存「訊息ID + 表情符號 = 身分組ID」的對應規則。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, total_exp INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS claims (message_id TEXT, user_id TEXT, PRIMARY KEY(message_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS reaction_roles (message_id TEXT, emoji TEXT, role_id TEXT, PRIMARY KEY(message_id, emoji))''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_state (key TEXT PRIMARY KEY, value TEXT)''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN combo INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN last_round INTEGER DEFAULT 0")
    except:
        pass

    conn.commit()
    conn.close()

# ==========================================
# 喝水經驗值與等級系統 (功能 A)
# ==========================================
def get_level_info(total_exp: int):
    """
    等級演算法：將使用者的「總經驗值」換算成當前等級進度。
    公式：每一級所需經驗值為 50 * 當前等級 + 50。
    回傳：(當前等級, 這一級已累積的經驗值, 升到下一級所需的經驗值)
    """
    level = 1
    current_exp = total_exp
    while True:
        req_exp = 50 * level + 50
        if current_exp >= req_exp:
            current_exp -= req_exp
            level += 1
        else:
            return level, current_exp, req_exp

def set_active_water_message(message_id: int):
    """更新當前最新的喝水通知 ID，並讓系統總回合數 + 1"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES ('active_water_message', ?)", (str(message_id),))
    
    # 讀取並更新當前總回合數 (Round)
    c.execute("SELECT value FROM system_state WHERE key = 'current_round'")
    result = c.fetchone()
    current_round = int(result[0]) if result else 0
    current_round += 1
    c.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES ('current_round', ?)", (str(current_round),))
    
    conn.commit()
    conn.close()

def get_current_round() -> int:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = 'current_round'")
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else 0

def claim_exp(message_id: int, user_id: int) -> tuple:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT 1 FROM claims WHERE message_id = ? AND user_id = ?", (str(message_id), str(user_id)))
    if c.fetchone():
        conn.close()
        return False, 0, 0, 0, 0  # ⚠️ 注意：這裡多加了一個 0，因為我們改變了回傳值的數量
        
    c.execute("INSERT INTO claims (message_id, user_id) VALUES (?, ?)", (str(message_id), str(user_id)))
    c.execute("SELECT total_exp, combo, last_round FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    
    current_round = get_current_round()
    
    if result:
        old_total = result[0]
        old_combo = result[1]
        last_round = result[2]
        
        # 判斷 Combo 是否延續
        if current_round == last_round + 1:
            new_combo = old_combo + 1
        else:
            new_combo = 1
            
        # 🌟 新增：每 5 Combo 額外加 5 經驗
        bonus_exp = 5 if (new_combo > 0 and new_combo % 5 == 0) else 0
        new_total = old_total + 10 + bonus_exp
            
        c.execute("UPDATE users SET total_exp = ?, combo = ?, last_round = ? WHERE user_id = ?", 
                  (new_total, new_combo, current_round, str(user_id)))
    else:
        old_total = 0
        new_total = 10
        new_combo = 1
        bonus_exp = 0
        c.execute("INSERT INTO users (user_id, total_exp, combo, last_round) VALUES (?, ?, ?, ?)", 
                  (str(user_id), 10, 1, current_round))
        
    conn.commit()
    conn.close()
    
    return True, old_total, new_total, new_combo, bonus_exp

def get_user_total_exp(user_id: int) -> int:
    """
    提供給 /rank 指令使用，單純查詢使用者的總經驗值。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_active_water_message() -> str:
    """取得當前有效的喝水通知 ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM system_state WHERE key = 'active_water_message'")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_full_data(user_id: int):
    """取得使用者的完整後台資料 (用於 /admin check)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_exp, combo, last_round FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    conn.close()
    # 回傳格式: (經驗值, Combo, 最後回合) 或 None
    return result

def remove_user_data(user_id: int):
    """徹底刪除使用者的所有資料 (用於 /admin remove_user)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 刪除使用者主表資料
    c.execute("DELETE FROM users WHERE user_id = ?", (str(user_id),))
    # 刪除該使用者的所有打卡紀錄
    c.execute("DELETE FROM claims WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

def reset_user_exp(user_id: int):
    """強制將使用者的經驗值、Combo、最後回合歸零"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 一併更新 combo 與 last_round
    c.execute("UPDATE users SET total_exp = 0, combo = 0, last_round = 0 WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

def get_total_participants_count() -> int:
    """取得參與修煉的總人數，用於計算總頁數"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_participants_paged(limit: int, offset: int):
    """取得特定範圍的參與人員資料 (分頁用)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 依照總經驗值降冪排序，並使用 LIMIT 與 OFFSET 進行分頁
    c.execute("SELECT user_id, total_exp FROM users ORDER BY total_exp DESC LIMIT ? OFFSET ?", (limit, offset))
    results = c.fetchall()
    conn.close()
    return results
# ==========================================
# 貼文反應身分組系統 (功能 B)
# ==========================================
def add_reaction_role(message_id: int, emoji: str, role_id: int):
    """
    提供給 !roleReact add 指令使用。
    將「哪則訊息」的「哪個表情符號」綁定「哪個身分組」存入資料庫。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO reaction_roles (message_id, emoji, role_id) VALUES (?, ?, ?)", 
              (str(message_id), str(emoji), str(role_id)))
    conn.commit()
    conn.close()

def get_role_by_reaction(message_id: int, emoji: str) -> int:
    """
    當使用者點擊表情符號時，查詢該表情對應的身分組 ID。
    回傳：身分組 ID (整數)，若找不到則回傳 None。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?", 
              (str(message_id), str(emoji)))
    result = c.fetchone()
    conn.close()
    return int(result[0]) if result else None

def get_all_roles_for_message(message_id: int):
    """
    查詢某一則訊息上綁定的「所有」身分組規則。
    主要用於「二選一互斥邏輯」，藉此找出使用者需要被移除的其他身分組。
    回傳格式：[(身分組ID, 表情符號), ...]
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role_id, emoji FROM reaction_roles WHERE message_id = ?", (str(message_id),))
    results = c.fetchall()
    conn.close()
    return results

def reset_user_exp(user_id: int):
    """
    將指定使用者的總經驗值、連續打卡數 (Combo) 與最後打卡回合強制歸零。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 將經驗值、combo、last_round 同步歸零
    c.execute("UPDATE users SET total_exp = 0, combo = 0, last_round = 0 WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

# ==========================================
# 管理員控制系統 (功能 C)
# ==========================================
def modify_user_exp(user_id: int, exp_amount: int, mode: str = "add") -> tuple:
    """
    提供給管理員指令使用，用於調整使用者經驗值。
    參數:
      - mode: "add" (增減，支援負數) 或 "set" (強制設定成指定數值)
    回傳:
      - (舊經驗值, 新經驗值)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 查詢使用者目前的資料
    c.execute("SELECT total_exp FROM users WHERE user_id = ?", (str(user_id),))
    result = c.fetchone()
    
    current_exp = result[0] if result else 0
    new_exp = current_exp
    
    if mode == "set":
        new_exp = exp_amount
    elif mode == "add":
        new_exp += exp_amount
        
    # 防止經驗值變成負數
    if new_exp < 0:
        new_exp = 0 
        
    if result:
        # 已經存在的使用者，直接更新 total_exp
        c.execute("UPDATE users SET total_exp = ? WHERE user_id = ?", (new_exp, str(user_id)))
    else:
        # 如果該名使用者從未打過卡，資料庫沒他的資料，則幫他建立一筆初始化資料
        c.execute("INSERT INTO users (user_id, total_exp, combo, last_round) VALUES (?, ?, 0, 0)", 
                  (str(user_id), new_exp))
        
    conn.commit()
    conn.close()
    return current_exp, new_exp