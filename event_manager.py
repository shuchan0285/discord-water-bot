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

    def get_random_event(self, fortune_buff=""):
        """
        根據權重與運勢 Buff 抽出一個隨機事件。
        大吉/吉：增加正向經驗機率，降低負向機率。
        凶：降低正向經驗機率，增加負向機率。
        """
        if not self.events:
            return None
            
        weights = []
        for e in self.events:
            base_w = e.get("weight", 1)
            exp_val = e.get("exp", 0)

            if fortune_buff == "大吉":
                if exp_val > 0: base_w *= 1.5
                elif exp_val < 0: base_w *= 0.5
            elif fortune_buff == "吉":
                if exp_val > 0: base_w *= 1.2
                elif exp_val < 0: base_w *= 0.8
            elif fortune_buff == "凶":
                if exp_val > 0: base_w *= 0.5
                elif exp_val < 0: base_w *= 1.5
            # 小吉/末吉/末小吉/已化解/空值，皆保持原始 base_w 權重 (乘以 1)

            weights.append(base_w)

        drawn = random.choices(self.events, weights=weights, k=1)[0]
        
        if drawn["id"] == "none":
            return None
            
        return drawn