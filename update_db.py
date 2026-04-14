import sqlite3

def upgrade_database():
    DB_NAME = "water_exp.db"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # 🌟 嘗試新增 daily_exp 欄位，預設值為 0
        c.execute("ALTER TABLE users ADD COLUMN daily_exp INTEGER DEFAULT 0")
        print("✅ 成功新增 daily_exp 欄位！資料庫升級完畢。")
    except sqlite3.OperationalError as e:
        # 如果出現錯誤 (通常是因為欄位已經存在)，則忽略
        if "duplicate column name" in str(e).lower():
            print("ℹ️ 欄位已經存在，無需更新。")
        else:
            print(f"⚠️ 發生錯誤：{e}")
    finally:
        # 無論成功或失敗，都確保儲存並關閉連線
        conn.commit()
        conn.close()

if __name__ == "__main__":
    upgrade_database()