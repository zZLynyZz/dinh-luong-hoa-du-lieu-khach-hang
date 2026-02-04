import pandas as pd
import re
import html
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
# CẤU HÌNH ĐƯỜNG DẪN & FILE
# ==============================================================================
BASE_DIR = project_root
INPUT_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
OUTPUT_PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

OUTPUT_MERGED_DEBUG = 'merged_raw.csv'
OUTPUT_FILENAME = 'processed_data.csv'

class DataProcessor:
    def __init__(self):
        """Khởi tạo Processor"""
        print("🔧 [PROCESSOR] Đang khởi tạo bộ xử lý dữ liệu...")
        
        # 1. Load Config & Dictionary
        self.config_loader = ConfigLoader.load()
        self.emoji_map = self.config_loader.emoji_map
        self.teencode_map = self.config_loader.teencode
        
        # 2. Compile Regex
        self.url_pattern = re.compile(r'http\S+|www\.\S+')
        self.regex_phone = re.compile(r'(03|05|07|08|09|01[2|6|8|9])+([0-9]{8})\b')
        self.regex_id = re.compile(r'\b\d{9}\b|\b\d{12}\b')
        self.regex_bank = re.compile(r'\b\d{10,16}\b')
        self.regex_email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.regex_money = re.compile(r'\b\d+([.,]\d+)*\s?(k|tr|triệu|đ|vnd|vnđ)\b', re.IGNORECASE)

    # --------------------------------------------------------------------------
    # 1. LOGIC MASKING PII
    # --------------------------------------------------------------------------
    def mask_pii_info(self, text):
        if not isinstance(text, str): return ""
        text = self.regex_phone.sub('[PHONE]', text)
        text = self.regex_id.sub('[ID_CARD]', text)
        text = self.regex_bank.sub('[BANK_ACC]', text)
        text = self.regex_email.sub('[EMAIL]', text)
        text = self.regex_money.sub('[MONEY]', text)
        return text

    # --------------------------------------------------------------------------
    # 2. LOGIC CHUẨN HÓA TEXT
    # --------------------------------------------------------------------------
    def normalize_text(self, text):
        if not isinstance(text, str): return ""

        text = str(text).lower()
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = self.url_pattern.sub('', text)

        for icon, token in self.emoji_map.items():
            if icon in text:
                text = text.replace(icon, f" {token} ")

        words = text.split()
        processed_words = [self.teencode_map.get(word, word) for word in words]
        text = ' '.join(processed_words)

        return re.sub(r'\s+', ' ', text).strip()

    # --------------------------------------------------------------------------
    # 3. HÀM ĐỌC VÀ GỘP FILE
    # --------------------------------------------------------------------------
    def load_and_merge_raw(self):
        if not os.path.exists(INPUT_RAW_DIR):
            print(f"❌ Lỗi: Thư mục không tồn tại: {INPUT_RAW_DIR}")
            return pd.DataFrame()

        all_files = [f for f in os.listdir(INPUT_RAW_DIR) if f.endswith('.csv')]
        
        if not all_files:
            print("⚠️ Cảnh báo: Không tìm thấy file .csv nào trong data/raw")
            return pd.DataFrame()

        print(f"📦 [PROCESSOR] Tìm thấy {len(all_files)} file nguồn: {all_files}")
        df_list = []
        
        for filename in all_files:
            try:
                path = os.path.join(INPUT_RAW_DIR, filename)
                df = pd.read_csv(path, encoding='utf-8-sig', on_bad_lines='skip', engine='python')
                
                if 'source_channel' not in df.columns:
                    df['source_channel'] = filename.replace('.csv', '')
                
                df_list.append(df)
            except Exception as e:
                print(f"❌ Lỗi đọc file {filename}: {e}")
        
        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)
            print(f"🔗 Đã gộp thành công. Tổng số dòng hợp lệ: {len(merged_df)}")
            return merged_df
        
        return pd.DataFrame()

    # --------------------------------------------------------------------------
    # 4. HÀM CHẠY CHÍNH 
    # --------------------------------------------------------------------------
    def run_process(self):
        print("\n🧹 [PROCESSOR] BẮT ĐẦU QUÁ TRÌNH XỬ LÝ DỮ LIỆU...")
        
        # 1. Load dữ liệu
        df = self.load_and_merge_raw()
        if df.empty:
            print("⏹️ Dừng quy trình vì không có dữ liệu.")
            return

        # --- [LOGIC MỚI] ĐÁNH LẠI SỐ THỨ TỰ (RE-INDEXING) ---
        print("   🔢 Đang tái lập chỉ mục (Re-indexing ID)...")
        # Xóa cột record_id cũ nếu có (để tránh trùng lặp hoặc lộn xộn)
        if 'record_id' in df.columns:
            df = df.drop(columns=['record_id'])
        
        # Tạo ID mới tinh, liền mạch: REC_001 -> REC_NNN
        df.insert(0, 'record_id', [f"REC_{i+1:03d}" for i in range(len(df))])
        # ----------------------------------------------------

        # 2. Lưu file gộp thô (merged_raw.csv) - Lúc này đã có ID mới chuẩn
        os.makedirs(OUTPUT_PROCESSED_DIR, exist_ok=True)
        debug_path = os.path.join(OUTPUT_PROCESSED_DIR, OUTPUT_MERGED_DEBUG)
        df.to_csv(debug_path, index=False, encoding='utf-8-sig')
        print(f"💾 [DEBUG] Đã lưu file gộp thô (ID mới) tại: {debug_path}")

        # 3. Xử lý Text
        def process_row(row):
            raw_text = row.get('original_text', '')
            if pd.isna(raw_text) or str(raw_text).strip() == '':
                return '[POST_REACTION]'
            text = self.mask_pii_info(str(raw_text))
            text = self.normalize_text(text)
            return text

        print("   ⚙️ Đang xử lý Text (Masking PII -> Emoji -> Teencode)...")
        df['processed_text'] = df.apply(process_row, axis=1)

        # 4. Chuẩn hóa Reaction
        if 'reaction_label' in df.columns:
             df['reaction_label'] = df['reaction_label'].fillna('NONE').astype(str).str.upper()

        # 5. Sắp xếp cột & Lưu file
        cols_order = [
            'record_id', 
            'timestamp', 
            'source_channel', 
            'social_user_id',   
            'original_text', 
            'processed_text',   
            'reaction_label'
        ]
        
        final_cols = [c for c in cols_order if c in df.columns]
        remaining_cols = [c for c in df.columns if c not in final_cols]
        df = df[final_cols + remaining_cols]

        output_path = os.path.join(OUTPUT_PROCESSED_DIR, OUTPUT_FILENAME)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ [PROCESSOR] Hoàn tất! File xử lý lưu tại: {output_path}")
        print("\n--- [PREVIEW] 5 DÒNG KẾT QUẢ ---")
        try:
            print(df[['record_id', 'processed_text']].head(5).to_string())
        except: pass

if __name__ == "__main__":
    processor = DataProcessor()
    processor.run_process()