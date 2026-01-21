import json
import yaml
import pandas as pd
import os

class SentimentScorer:
    def __init__(self, resource_path='resources'):
        """
        Khởi tạo bộ chấm điểm, nạp Config và Từ điển.
        """
        self.resource_path = resource_path
        
        # 1. Load Config (Trọng số & Điểm Reaction)
        # File config.yaml chứa: weights, reaction_scores, emoji_scores, thresholds
        try:
            with open(f"{resource_path}/config.yaml", 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print("❌ Lỗi nghiêm trọng: Không tìm thấy file resources/config.yaml")
            self.config = {}

        # 2. Load Từ điển Cảm xúc (Text Sentiment)
        # File sentiment_keywords.json chứa: panic, negative, positive...
        try:
            with open(f"{resource_path}/dictionaries/sentiment_keywords.json", 'r', encoding='utf-8') as f:
                self.sentiment_dict = json.load(f)
        except FileNotFoundError:
            print("⚠️ Cảnh báo: Không tìm thấy sentiment_keywords.json")
            self.sentiment_dict = {}

        # 3. Lấy điểm Emoji từ Config
        self.emoji_scores = self.config.get('emoji_scores', {})

    def calculate_text_score(self, text):
        """
        Tính điểm text dựa trên từ khóa và emoji token.
        """
        if not isinstance(text, str) or text == '[POST_REACTION]':
            return 0.0

        score = 0.0
        text_lower = text.lower()

        # 1. Cộng điểm từ khóa
        for sentiment_type, data in self.sentiment_dict.items():
            base_score = data.get('score', 0)
            keywords = data.get('keywords', [])
            
            for kw in keywords:
                if kw in text_lower:
                    score += base_score

        # 2. Cộng điểm Emoji Token (VD: [ICON_POS])
        for token, emoji_score in self.emoji_scores.items():
            if token.lower() in text_lower:
                score += emoji_score

        # 3. Giới hạn điểm (Clamping) trong khoảng [-2, +2]
        system_conf = self.config.get('system', {})
        max_score = system_conf.get('max_score', 2.0)
        min_score = system_conf.get('min_score', -2.0)
        
        return max(min(score, max_score), min_score)

    def calculate_final_score(self, text_score, reaction_score, is_split):
        """
        Logic tính điểm tổng hợp (Core Logic)
        """
        # --- QUY TẮC 1: Tín hiệu Im lặng (Post Reaction) ---
        # Khách không nói gì, chỉ thả Reaction
        if text_score == 0 and reaction_score != 0:
            return reaction_score

        # --- QUY TẮC BỔ SUNG: Xử lý câu bị tách (Split Polarity Logic) ---
        # Nếu câu bị tách (is_split=True), Reaction tiêu cực KHÔNG được làm hỏng đoạn text tích cực
        effective_reaction_score = reaction_score
        
        if is_split:
            # Tình huống: Khen "Lãi ngon" (+1) nhưng lại dính Reaction ANGRY (-2) của vế sau
            if text_score > 0 and reaction_score < 0:
                effective_reaction_score = 0.0  # Vô hiệu hóa reaction cho đoạn này

        # --- QUY TẮC 2: Phát hiện Mỉa mai (Sarcasm) ---
        # Chỉ áp dụng cho câu nguyên bản (không bị tách) hoặc khi reaction vẫn hợp lệ
        # Tình huống: Text khen (+2) nhưng thả HAHA/ANGRY (-0.5/-2) -> Lấy điểm Reaction
        if text_score > 0 and effective_reaction_score < 0:
            return effective_reaction_score

        # --- QUY TẮC 3: Cộng hưởng (Weighted Average) ---
        weights = self.config.get('weights', {'text_content': 0.7, 'reaction': 0.3})
        w_text = weights.get('text_content', 0.7)
        w_react = weights.get('reaction', 0.3)
        
        final = (text_score * w_text) + (effective_reaction_score * w_react)
        
        return round(final, 2)

    def assign_label(self, score):
        """ Gán nhãn chữ dựa trên điểm số """
        thresholds = self.config.get('priority_thresholds', {})
        
        if score <= thresholds.get('critical', -2.0):
            return "PANIC"     # Rất nguy hiểm
        elif score <= thresholds.get('high', -1.0):
            return "NEGATIVE"  # Tiêu cực
        elif score < 0:
            return "SKEPTICAL" # Nghi ngờ/Hơi tiêu cực
        elif score >= 1.5:
            return "ADVOCACY"  # Ủng hộ mạnh
        elif score > 0:
            return "POSITIVE"  # Tích cực
        else:
            return "NEUTRAL"   # Trung tính

    def assign_priority(self, row):
        """
        [cite_start]Xác định mức độ ưu tiên xử lý (SLA) dựa trên Label và Topic [cite: 177-178]
        """
        score = row.get('final_score', 0)
        topic = row.get('topic_code', 'TOPIC_OTHER')
        
        # 1. CRITICAL: Liên quan đến Niềm tin (Lừa đảo) hoặc Điểm liệt (-2)
        if topic == 'TOPIC_TRUST' or score <= -2.0:
            return 'CRITICAL'
            
        # 2. HIGH: Liên quan đến Tiền nong (Nạp/Rút) mà bị lỗi
        if topic in ['TOPIC_DEPOSIT', 'TOPIC_WITHDRAW'] and score <= -1.0:
            return 'HIGH'
            
        # 3. MEDIUM: Liên quan tài khoản (eKYC)
        if topic == 'TOPIC_EKYC' and score < 0:
            return 'MEDIUM'
            
        # 4. OPPORTUNITY: Khen sản phẩm -> Cơ hội marketing
        if topic == 'TOPIC_PRODUCT' and score >= 1.5:
            return 'OPPORTUNITY'
            
        return 'NORMAL'

    def run(self, df):
        print("🧮 Đang thực hiện Giai đoạn 3 (Bước 3): Chấm điểm (Scoring)...")
        output_rows = []
        
        for index, row in df.iterrows():
            # Lấy dữ liệu
            text = row.get('segment_content', '')
            reaction_label = row.get('reaction_label', 'NONE')
            is_split = row.get('is_split', False)
            
            # Tính điểm
            s_text = self.calculate_text_score(text)
            
            # Lấy điểm reaction từ config (Ví dụ: LOVE -> 2.0, 5_STAR -> 2.0)
            reaction_map = self.config.get('reaction_scores', {})
            s_react = reaction_map.get(reaction_label, 0.0)

            # Tính điểm tổng
            final_score = self.calculate_final_score(s_text, s_react, is_split)
            
            # Gán nhãn
            sentiment_label = self.assign_label(final_score)

            # Đóng gói kết quả
            new_row = row.to_dict()
            new_row['text_score'] = s_text
            new_row['reaction_score'] = s_react
            new_row['final_score'] = final_score
            new_row['sentiment_label'] = sentiment_label
            
            output_rows.append(new_row)

        scored_df = pd.DataFrame(output_rows)
        
        # Gán thêm cột Priority (Mức độ ưu tiên xử lý)
        scored_df['priority_level'] = scored_df.apply(self.assign_priority, axis=1)
        
        print(f"✅ Đã chấm điểm xong {len(scored_df)} dòng.")
        return scored_df

# --- PHẦN CHẠY THỰC TẾ VỚI FILE ---
if __name__ == "__main__":
    # 1. Định nghĩa đường dẫn
    input_path = 'data/processed/classified_segments.csv'       # Đầu vào từ bước Topic
    output_path = 'data/output/SCORED_FEEDBACK_SEGMENTS.csv'    # ĐẦU RA CUỐI CÙNG
    
    # Tạo thư mục output nếu chưa có
    os.makedirs('data/output', exist_ok=True)

    if not os.path.exists(input_path):
        print(f"❌ Lỗi: Không tìm thấy file {input_path}")
        print("👉 Hãy chạy topic_classifier.py trước!")
    else:
        try:
            # 2. Đọc dữ liệu
            df_classified = pd.read_csv(input_path, encoding='utf-8-sig')
            
            # 3. Chạy Scorer
            scorer = SentimentScorer(resource_path='resources')
            df_result = scorer.run(df_classified)

            # 4. Xuất file kết quả cuối cùng
            df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"\n🎉🎉🎉 CHÚC MỪNG! Dữ liệu đã được xử lý hoàn tất.")
            print(f"📄 File kết quả nằm tại: {output_path}")

            # 5. Soi kết quả: Chọn các cột quan trọng nhất để hiển thị
            print("\n--- PREVIEW KẾT QUẢ CUỐI CÙNG ---")
            cols_show = [
                'segment_content', 'topic_code', 'reaction_label', 
                'final_score', 'sentiment_label', 'priority_level'
            ]
            
            # Sắp xếp để xem những cái Tiêu cực/Nghiêm trọng lên đầu
            df_sorted = df_result.sort_values(by='final_score')
            print(df_sorted[cols_show].head(10).to_string())

        except Exception as e:
            print(f"❌ Có lỗi xảy ra: {e}")