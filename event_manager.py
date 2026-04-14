# event_manager.py
import json
import random
import os

class EventManager:
    def __init__(self):
        self.events = []
        self.load_events()

    def load_events(self):
        file_path = "events.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.events = json.load(f)
                print(f"✅ 成功載入 {len(self.events)} 種隨機事件。")
        except Exception as e:
            print(f"❌ 讀取 events.json 失敗: {e}")

    def get_random_event(self):
        """
        根據權重抽出一個隨機事件。
        如果是 'none' (無事發生)，則回傳 None。
        """
        if not self.events:
            return None
            
        weights = [e.get("weight", 1) for e in self.events]
        # random.choices 會回傳一個 list，我們取第 0 個元素
        drawn = random.choices(self.events, weights=weights, k=1)[0]
        
        if drawn["id"] == "none":
            return None
            
        return drawn