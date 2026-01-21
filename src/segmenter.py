import json
import re
import pandas as pd
import os

class DataSegmenter:
    def __init__(self, dict_path='resources/dictionaries'):
        self.dict_path = dict_path
        # Load từ điển
        try:
            with open(f"{dict_path}/pivot_keywords.json", 'r', encoding='utf-8') as f:
                self.pivot_keywords = json.load(f)
                # Sắp xếp từ dài lên trước để ưu tiên khớp chính xác
                self.pivot_keywords.sort(key=len, reverse=True)
        except FileNotFoundError:
            print("⚠️ Cảnh báo: Không tìm thấy pivot_keywords.json")
            self.pivot_keywords = []

        # Xây dựng Regex: Dùng (?:...) để KHÔNG giữ lại từ khóa trong kết quả
        # Logic: Tìm các từ khóa này trong văn bản để làm điểm cắt
        if self.pivot_keywords:
            self.pattern = r'(?:' + '|'.join([re.escape(k) for k in self.pivot_keywords]) + r')'
        else:
            self.pattern = None

    def split_text(self, text):
        """
        Hàm tách chuỗi dựa trên từ khóa đảo chiều (nhưng, tuy nhiên...)
        """
        # 1. Kiểm tra đầu vào
        if not isinstance(text, str) or text.strip() == "" or text == '[POST_REACTION]':
            return [text]

        if not self.pattern:
            return [text]

        # 2. Thực hiện tách (Split)
        # Vì đã dùng (?:) nên re.split sẽ nuốt luôn từ khóa nối, trả về các đoạn văn
        segments = re.split(self.pattern, text)
        
        # 3. Làm sạch kết quả
        cleaned_segments = []
        for seg in segments:
            seg = seg.strip() # Chỉ cắt khoảng trắng thừa, giữ lại dấu chấm câu
            if seg:
                cleaned_segments.append(seg)
        
        # Trả về kết quả (nếu list rỗng thì trả về list chứa text gốc)
        return cleaned_segments if cleaned_segments else [text]

    def run(self, df):
        print("✂️  Đang thực hiện Giai đoạn 3 (Bước 1): Tách đoạn theo từ khóa mâu thuẫn...")
        output_rows = []

        for index, row in df.iterrows():
            original_text = row.get('processed_text', '')
            parent_id = row.get('record_id', f'REC_{index}')
            
            # Tách câu
            segments = self.split_text(original_text)
            
            # Kiểm tra xem có tách không
            is_split = len(segments) > 1

            for i, seg_content in enumerate(segments):
                new_row = row.to_dict()
                new_row['segment_id'] = f"{parent_id}_{i}"
                new_row['parent_id'] = parent_id
                new_row['segment_content'] = seg_content
                new_row['is_split'] = is_split # True nếu câu có từ "nhưng", False nếu chỉ có dấu chấm
                output_rows.append(new_row)

        segmented_df = pd.DataFrame(output_rows)
        print(f"✅ Đã xử lý {len(df)} dòng -> {len(segmented_df)} đoạn.")
        return segmented_df

# --- CODE TEST (Chạy với dữ liệu thật từ Giai đoạn 2) ---
if __name__ == "__main__":
    # 1. Đường dẫn file (Lấy từ kết quả GĐ2)
    input_path = 'data/processed/cleaned_comments.csv'
    output_path = 'data/processed/segmented_comments.csv'

    if not os.path.exists(input_path):
        print(f"❌ Không tìm thấy file {input_path}. Hãy chạy preprocessor.py trước!")
    else:
        try:
            # 2. Đọc file
            df_processed = pd.read_csv(input_path, encoding='utf-8-sig')
            
            # 3. Chạy Segmenter
            segmenter = DataSegmenter(dict_path='resources/dictionaries')
            df_result = segmenter.run(df_processed)

            # 4. Lưu kết quả
            df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # 5. Soi kết quả: Chỉ in những dòng BỊ TÁCH
            print("\n--- CÁC CÂU BỊ TÁCH (Có mâu thuẫn) ---")
            split_rows = df_result[df_result['is_split'] == True]
            if not split_rows.empty:
                print(split_rows[['parent_id', 'segment_content']].head(10).to_string())
            else:
                print("Không có câu nào chứa từ khóa mâu thuẫn (nhưng, tuy nhiên...).")
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")