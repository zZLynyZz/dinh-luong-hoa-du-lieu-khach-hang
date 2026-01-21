# Module Giai doan 3: Gan chu de
import json
import pandas as pd
import os

class TopicClassifier:
    def __init__(self, dict_path='resources/dictionaries'):
        """
        Khởi tạo, load từ điển Topic Keywords.
        """
        self.dict_path = dict_path
        try:
            with open(f"{dict_path}/topic_keywords.json", 'r', encoding='utf-8') as f:
                self.topic_dict = json.load(f)
        except FileNotFoundError:
            print("⚠️ Cảnh báo: Không tìm thấy topic_keywords.json")
            self.topic_dict = {}

    def classify_text(self, text):
        """
        Hàm quét từ khóa để xác định Topic.
        Input: "nạp tiền mãi không được"
        Output: "TOPIC_DEPOSIT"
        """
        if not isinstance(text, str) or text.strip() == "":
            return "TOPIC_OTHER" # Mặc định nếu không tìm thấy gì

        text_lower = text.lower()

        # Duyệt qua từng chủ đề trong từ điển
        # Lưu ý: Thứ tự ưu tiên phụ thuộc vào thứ tự trong file JSON
        for topic_code, keywords in self.topic_dict.items():
            for kw in keywords:
                # Kiểm tra từ khóa có trong văn bản không
                if kw in text_lower:
                    return topic_code
        
        return "TOPIC_OTHER" # Không khớp từ khóa nào

    def process_row(self, row):
        """
        Logic chọn dữ liệu đầu vào để phân loại
        """
        segment_content = row.get('segment_content', '')
        context_content = row.get('context_content', '')
        
        # LOGIC QUAN TRỌNG: Xử lý Post Reaction [cite: 58, 183]
        # Nếu segment_content là [POST_REACTION], ta phải soi context_content (bài post)
        if segment_content == '[POST_REACTION]':
            target_text = str(context_content)
        else:
            # Trường hợp bình thường: Soi nội dung comment đã tách
            target_text = str(segment_content)
            
        return self.classify_text(target_text)

    def run(self, df):
        """
        Hàm chạy chính cho DataFrame
        """
        print("🏷️  Đang thực hiện Giai đoạn 3 (Bước 2): Phân loại Chủ đề (Topic Classification)...")
        
        # Tạo bản sao để tránh warning
        classified_df = df.copy()
        
        # Áp dụng logic phân loại
        classified_df['topic_code'] = classified_df.apply(self.process_row, axis=1)
        
        print(f"✅ Đã gán chủ đề cho {len(classified_df)} đoạn dữ liệu.")
        return classified_df

# --- CODE TEST (Chạy với dữ liệu đã tách câu từ bước trước) ---
if __name__ == "__main__":
    # 1. Định nghĩa đường dẫn
    input_path = 'data/processed/segmented_comments.csv'    # Đầu vào từ Segmenter
    output_path = 'data/processed/classified_segments.csv'  # Đầu ra của bước này

    if not os.path.exists(input_path):
        print(f"❌ Không tìm thấy file {input_path}. Hãy chạy segmenter.py trước!")
    else:
        try:
            # 2. Đọc dữ liệu
            df_segmented = pd.read_csv(input_path, encoding='utf-8-sig')
            
            # 3. Khởi tạo và chạy Classifier
            classifier = TopicClassifier(dict_path='resources/dictionaries')
            df_result = classifier.run(df_segmented)

            # 4. Lưu kết quả
            df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # 5. Soi kết quả: In ra để kiểm tra tính đúng đắn
            print("\n--- KẾT QUẢ PHÂN LOẠI CHỦ ĐỀ ---")
            
            # Chọn các cột quan trọng để hiển thị
            cols_show = ['segment_content', 'context_content', 'topic_code']
            
            # Lọc vài case điển hình để xem
            # Case 1: Post Reaction (Phải lấy topic từ context)
            post_reacts = df_result[df_result['segment_content'] == '[POST_REACTION]']
            if not post_reacts.empty:
                print("\n👉 Case Post Reaction (Topic từ Context):")
                print(post_reacts[cols_show].head(2).to_string())

            # Case 2: Comment thường
            normal_cmts = df_result[df_result['segment_content'] != '[POST_REACTION]']
            print("\n👉 Case Comment thường (Topic từ Content):")
            print(normal_cmts[cols_show].head(5).to_string())

        except Exception as e:
            print(f"❌ Lỗi: {e}")