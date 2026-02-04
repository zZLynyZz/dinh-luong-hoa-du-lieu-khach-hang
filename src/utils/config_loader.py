import yaml
import json
import os
import sys

# Tìm đường dẫn gốc dự án
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

class ConfigLoader:
    _instance = None

    def __init__(self):
        self.resource_path = os.path.join(project_root, 'resources')
        self.dict_path = os.path.join(self.resource_path, 'dictionaries')
        
        # 1. Load Config YAML
        self.config = self._load_yaml_config()
        
        # 2. Load các từ điển CỐ ĐỊNH (Dùng thường xuyên)
        self.emoji_map = self._load_json_dict('emoji_map.json')
        self.teencode = self._load_json_dict('teencode.json')
        
        # 👇 [MỚI] Load Reaction Map để dùng bên DataMerger
        self.reaction_map = self._load_json_dict('reaction_map.json')
        
        # 3. Load kho từ điển cho Scorer (Load vào dict tổng)
        self.dictionaries = {
            'sentiment_keywords': self._load_json_dict('sentiment_keywords.json'),
            'topic_keywords': self._load_json_dict('topic_keywords.json'),
            'pivot_keywords': self._load_json_dict('pivot_keywords.json')
        }
        
        print(f"✅ [CONFIG] Đã tải: config.yaml")
        print(f"✅ [CONFIG] Đã tải Reaction Map: {len(self.reaction_map)} rules.")
        print(f"✅ [CONFIG] Đã tải {len(self.dictionaries) + 2} bộ từ điển khác.")

    @classmethod
    def load(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_yaml_config(self):
        try:
            config_path = os.path.join(self.resource_path, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Lỗi load config.yaml: {e}")
            return {}

    def _load_json_dict(self, filename):
        try:
            path = os.path.join(self.dict_path, filename)
            if not os.path.exists(path):
                # print(f"⚠️ Không tìm thấy từ điển: {filename}")
                return {} if filename != 'pivot_keywords.json' else []
            
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Lỗi load {filename}: {e}")
            return {}

    def get_dict(self, key):
        """Lấy từ điển theo key (hỗ trợ lazy load cho Scorer)"""
        if key in self.dictionaries:
            return self.dictionaries[key]
        
        # Fallback: Nếu chưa có trong list thì thử tìm file load lên
        if not key.endswith('.json'):
            key += '.json'
        return self._load_json_dict(key)