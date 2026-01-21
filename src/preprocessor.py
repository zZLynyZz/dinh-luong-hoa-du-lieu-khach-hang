import re
import json
import pandas as pd
import html
import os

class DataPreprocessor:
    def __init__(self, dict_path='resources/dictionaries'):
        """
        Khởi tạo Preprocessor, load các từ điển cần thiết từ file JSON.
        """
        self.dict_path = dict_path
        
        # 1. Load Emoji Map
        try:
            with open(f"{dict_path}/emoji_map.json", 'r', encoding='utf-8') as f:
                self.emoji_map = json.load(f)
        except FileNotFoundError:
            print("⚠️ Cảnh báo: Không tìm thấy emoji_map.json")
            self.emoji_map = {}

        # 2. Load Teencode Map 
        try:
            with open(f"{dict_path}/teencode.json", 'r', encoding='utf-8') as f:
                self.teencode_map = json.load(f)
        except FileNotFoundError:
            print("⚠️ Cảnh báo: Không tìm thấy teencode.json, dùng từ điển rỗng.")
            self.teencode_map = {}

    def mask_pii_info(self, text):
        """ Giai đoạn 2 - Mục 2: Masking thông tin nhạy cảm  """
        if not isinstance(text, str):
            return ""
        
        # 1. Số điện thoại (09xx, 03xx...) 
        # Regex bắt các đầu số VN phổ biến 10 số
        text = re.sub(r'(03|05|07|08|09|01[2|6|8|9])+([0-9]{8})\b', '[PHONE]', text)
        
        # 2. Số CCCD/CMND (9 hoặc 12 số) 
        text = re.sub(r'\b\d{9}\b|\b\d{12}\b', '[ID_CARD]', text)
        
        # 3. Số tài khoản ngân hàng (9-16 số, thường đi sau chữ stk, ck...) 
        # Regex này bắt chuỗi số dài đứng độc lập
        text = re.sub(r'\b\d{10,16}\b', '[BANK_ACC]', text)
        
        # 4. Email 
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # 5. Số tiền cụ thể (500k, 10tr...) 
        # Bắt: 500k, 100tr, 10.000đ, 100,000 VND
        text = re.sub(r'\b\d+([.,]\d+)*\s?(k|tr|triệu|đ|vnd|vnđ)\b', '[MONEY_AMOUNT]', text, flags=re.IGNORECASE)

        return text

    def normalize_text(self, text):
        """ Giai đoạn 2 - Mục 3: Chuẩn hóa văn bản  """
        if not isinstance(text, str):
            return ""

        # 1. Chuyển về chữ thường 
        text = text.lower()

        # 2. Xóa HTML tags và decode HTML entities (&amp; -> &) 
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)

        # 3. Xóa URL rác
        text = re.sub(r'http\S+|www.\S+', '', text)

        # Thay thế Teencode bằng từ điển đã load
        words = text.split()
        # Logic thay thế: Nếu từ có trong dict thì thay, không thì giữ nguyên
        processed_words = [self.teencode_map.get(word, word) for word in words]
        text = ' '.join(processed_words)

        return text

    def convert_emoji_to_token(self, text):
        """ Giai đoạn 2 - Mục 4: Emoji to Token  """
        if not isinstance(text, str):
            return ""
            
        for emoji_char, token in self.emoji_map.items():
            if emoji_char in text:
                text = text.replace(emoji_char, f" {token} ")
        
        return re.sub(r'\s+', ' ', text).strip()

    def process_row(self, row):
        """ Xử lý từng dòng dữ liệu """
        original_text = row.get('original_text', '')
        source_channel = row.get('source_channel', '')
        
        # Logic xử lý Post Reaction (User không comment) 
        is_post_reaction = pd.isna(original_text) or str(original_text).strip() == '' or 'Post_React' in str(source_channel)
        
        if is_post_reaction:
            return '[POST_REACTION]'
        
        # Pipeline xử lý text thông thường
        text = self.mask_pii_info(str(original_text))
        text = self.normalize_text(text)
        text = self.convert_emoji_to_token(text)
        
        return text

    def run(self, df):
        """ Hàm chạy chính cho toàn bộ DataFrame """
        print("🧹 Đang thực hiện Giai đoạn 2: Làm sạch và Chuẩn hóa...")
        processed_df = df.copy()
        processed_df['processed_text'] = processed_df.apply(self.process_row, axis=1)
        
        # Chuẩn hóa nhãn Reaction về chữ hoa (LOVE, ANGRY...)
        if 'reaction_label' in processed_df.columns:
            processed_df['reaction_label'] = processed_df['reaction_label'].fillna('NONE').astype(str).str.upper()
        
        return processed_df

# --- PHẦN CHẠY THỰC TẾ (MAIN) ---
if __name__ == "__main__":
    # 1. Định nghĩa đường dẫn file
    input_path = 'data/raw/raw_comments.csv'       # File CSV bịa lúc nãy
    output_path = 'data/processed/cleaned_comments.csv' # File kết quả GĐ2
    
    # Kiểm tra xem file đầu vào có tồn tại không
    if not os.path.exists(input_path):
        print(f"❌ Lỗi: Không tìm thấy file {input_path}. Hãy tạo file này trước!")
    else:
        try:
            # 2. Đọc dữ liệu thô
            # Dùng encoding='utf-8-sig' để đọc file tiếng Việt ko bị lỗi
            df_raw = pd.read_csv(input_path, encoding='utf-8-sig')
            print(f"📂 Đã đọc {len(df_raw)} dòng dữ liệu từ {input_path}")

            # 3. Khởi tạo và chạy Preprocessor
            preprocessor = DataPreprocessor(dict_path='resources/dictionaries')
            df_clean = preprocessor.run(df_raw)

            # 4. Xuất kết quả ra file mới
            # Tạo thư mục nếu chưa có
            os.makedirs('data/processed', exist_ok=True)
            df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"✅ XỬ LÝ THÀNH CÔNG!")
            print(f"📄 Kết quả Giai đoạn 2 đã được lưu tại: {output_path}")
            
            # In thử 5 dòng đầu để kiểm tra
            print("\n--- PREVIEW KẾT QUẢ (5 dòng đầu) ---")
            print(df_clean[['original_text', 'processed_text']].head().to_string())
            
        except Exception as e:
            print(f"❌ Có lỗi xảy ra: {e}")