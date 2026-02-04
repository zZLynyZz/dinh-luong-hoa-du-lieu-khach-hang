import pandas as pd
import re
import os
import sys

# ==============================================================================
# [HEADER FIX PATH]
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) 
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import ConfigLoader

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
BASE_DIR = project_root
INPUT_CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_REPORT_DIR = os.path.join(BASE_DIR, 'data', 'reports')

INPUT_FILENAME = 'processed_data.csv'      
OUTPUT_FILENAME = 'final_sentiment_report.csv'

class SentimentScorer:
    def __init__(self):
        print("🔧 [SCORER] Đang khởi tạo bộ chấm điểm...")
        self.config_loader = ConfigLoader.load()
        self.config = self.config_loader.config
        
        # 1. Load config
        self.weights = self.config.get('weights', {'text_content': 0.7, 'reaction': 0.3})
        self.reaction_scores = self.config.get('reaction_scores', {})
        self.emoji_scores = self.config.get('emoji_scores', {})
        self.thresholds = self.config.get('priority_thresholds', {})
        
        # 2. Load dict
        self.sentiment_keywords = self.config_loader.get_dict('sentiment_keywords')
        self.topic_keywords = self.config_loader.get_dict('topic_keywords')
        self.pivot_keywords = self.config_loader.get_dict('pivot_keywords')
        
        # 3. Regex tách câu
        if self.pivot_keywords:
            sorted_pivots = sorted(self.pivot_keywords, key=len, reverse=True)
            self.split_pattern = r'(?:' + '|'.join([re.escape(k) for k in sorted_pivots]) + r')'
        else:
            self.split_pattern = None

    # --------------------------------------------------------------------------
    # 1. LOGIC TÁCH ĐOẠN
    # --------------------------------------------------------------------------
    def split_text(self, text):
        if not isinstance(text, str) or not text.strip(): return [text]
        if text == '[POST_REACTION]': return [text]
        if not self.split_pattern: return [text]

        raw_segments = re.split(self.split_pattern, text)
        segments = [seg.strip() for seg in raw_segments if seg.strip()]
        return segments if segments else [text]

    # --------------------------------------------------------------------------
    # 2. LOGIC TÍNH ĐIỂM TEXT
    # --------------------------------------------------------------------------
    def calculate_text_score(self, text):
        if text == '[POST_REACTION]': return 0.0
        score = 0.0
        text_lower = text.lower()
        
        for label, data in self.sentiment_keywords.items():
            base_score = data['score']
            for kw in data['keywords']:
                if kw in text_lower:
                    score += base_score
        
        for token, val in self.emoji_scores.items():
            count = text.count(token)
            if count > 0: score += (val * count)
        
        return max(-2.0, min(2.0, score))

    # --------------------------------------------------------------------------
    # 3. LOGIC TOPIC
    # --------------------------------------------------------------------------
    def detect_topic(self, text, context_content=None):
        target_text = text
        # Nếu là reaction, dùng context để detect topic
        if text == '[POST_REACTION]':
            if pd.isna(context_content) or str(context_content).strip() == "":
                return 'TOPIC_OTHER'
            target_text = str(context_content)
        
        target_text_lower = str(target_text).lower()
        detected_topics = []
        for topic, keywords in self.topic_keywords.items():
            for kw in keywords:
                if kw in target_text_lower:
                    detected_topics.append(topic)
                    break 
        if not detected_topics: return 'TOPIC_OTHER'
        return detected_topics[0]

    # --------------------------------------------------------------------------
    # 4. LOGIC ĐIỂM FINAL
    # --------------------------------------------------------------------------
    def calculate_final_score(self, text_score, reaction_score, is_split):
        if text_score == 0 and reaction_score != 0: return reaction_score
        
        effective_reaction = reaction_score
        if is_split:
            if text_score > 0 and reaction_score < 0:
                effective_reaction = 0.0

        if text_score > 0 and effective_reaction < 0:
            return effective_reaction

        w_text = self.weights.get('text_content', 0.7)
        w_react = self.weights.get('reaction', 0.3)
        final = (text_score * w_text) + (effective_reaction * w_react)
        return round(final, 2)

    # --------------------------------------------------------------------------
    # 5. LOGIC LABEL & PRIORITY
    # --------------------------------------------------------------------------
    def assign_label(self, score):
        if score <= self.thresholds.get('critical', -2.0): return "PANIC"
        elif score <= self.thresholds.get('high', -1.0): return "NEGATIVE"
        elif score < 0: return "SKEPTICAL"
        elif score >= 1.5: return "ADVOCACY"
        elif score > 0: return "POSITIVE"
        else: return "NEUTRAL"

    def assign_priority(self, score, topic):
        if topic == 'TOPIC_TRUST' or score <= -2.0: return 'CRITICAL'
        if topic in ['TOPIC_DEPOSIT', 'TOPIC_WITHDRAW'] and score <= -1.0: return 'HIGH'
        if topic == 'TOPIC_EKYC' and score < 0: return 'MEDIUM'
        if topic == 'TOPIC_PRODUCT' and score >= 1.5: return 'OPPORTUNITY'
        return 'NORMAL'

    # --------------------------------------------------------------------------
    # 6. MAIN RUN
    # --------------------------------------------------------------------------
    def run_analysis(self):
        print("\n📊 [SCORER] BẮT ĐẦU CHẤM ĐIỂM CHI TIẾT...")
        
        input_path = os.path.join(INPUT_CLEAN_DIR, INPUT_FILENAME)
        if not os.path.exists(input_path):
            print(f"❌ Lỗi: Không tìm thấy file {input_path}")
            return
            
        df = pd.read_csv(input_path, encoding='utf-8-sig')
        print(f"   ↳ Đã đọc {len(df)} dòng dữ liệu.")
        
        results = []

        for idx, row in df.iterrows():
            record_id = str(row.get('record_id', ''))
            processed_text = row.get('processed_text', '') 
            reaction_label = row.get('reaction_label', 'NONE')
            context_content = row.get('context_content', '')
            social_user = row.get('social_user_id', '')
            created_time = row.get('timestamp', '')
            
            # --- TÁCH ĐOẠN ---
            segments = self.split_text(processed_text)
            is_split = len(segments) > 1
            
            # --- LẤY SỐ HIỆU ID (VD: 015) ---
            try:
                rec_suffix = record_id.split('_')[-1]
            except:
                rec_suffix = record_id

            # --- VÒNG LẶP XỬ LÝ ---
            for i, seg in enumerate(segments):
                # 1. TẠO SEGMENT ID (A, B, C...)
                if is_split:
                    letter_suffix = chr(65 + i) 
                    segment_id = f"SEG_{rec_suffix}_{letter_suffix}"
                else:
                    segment_id = f"SEG_{rec_suffix}"

                # 2. TÍNH TOÁN
                s_text = self.calculate_text_score(seg)
                s_react = self.reaction_scores.get(reaction_label, 0.0)
                final_score = self.calculate_final_score(s_text, s_react, is_split)
                topic = self.detect_topic(seg, context_content)
                label = self.assign_label(final_score)
                priority = self.assign_priority(final_score, topic)
                
                # 3. [UPDATE] LOGIC HIỂN THỊ NỘI DUNG (Content Logic)
                # Nếu là Reaction -> Hiển thị Nội dung bài Post (Context)
                # Nếu là Comment  -> Hiển thị Comment của khách (Segment)
                display_content = seg
                if seg == '[POST_REACTION]':
                    display_content = context_content

                # 4. ĐÓNG GÓI
                results.append({
                    'segment_id': segment_id,
                    'original_record_id': record_id,
                    'social_user_id': social_user,
                    'created_time': created_time,
                    'segment_content': display_content, # <-- Dùng biến hiển thị mới
                    'is_split': is_split,
                    'topic_code': topic,
                    'reaction_label': reaction_label,
                    'score_text': s_text,
                    'score_react': s_react,
                    'final_score': final_score,
                    'sentiment_label': label,
                    'priority_level': priority
                })

        # --- LƯU FILE ---
        df_result = pd.DataFrame(results)
        
        cols_order = [
            'segment_id', 'original_record_id', 'social_user_id', 'created_time', 
            'segment_content', 'is_split', 'topic_code', 'reaction_label', 
            'score_text', 'score_react', 'final_score', 'sentiment_label', 'priority_level'
        ]
        final_cols = [c for c in cols_order if c in df_result.columns]
        df_result = df_result[final_cols]

        os.makedirs(OUTPUT_REPORT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_REPORT_DIR, OUTPUT_FILENAME)
        
        # Sắp xếp theo ID
        print("   🔢 Đang sắp xếp kết quả theo thứ tự ID...")
        df_result = df_result.sort_values(by=['original_record_id', 'segment_id'])

        df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ [SCORER] Hoàn tất! Báo cáo chi tiết tại: {output_path}")
        print("\n--- [PREVIEW] KẾT QUẢ ---")
        try:
            # Preview segment_content để kiểm tra xem đã hiện content bài post chưa
            print(df_result[['segment_id', 'segment_content', 'reaction_label']].head(5).to_string(index=False))
        except: pass

if __name__ == "__main__":
    scorer = SentimentScorer()
    scorer.run_analysis()