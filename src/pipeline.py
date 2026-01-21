import pandas as pd
import os
import sys

# Import các module đã xây dựng
# (Đảm bảo file __init__.py đã có trong thư mục src để Python hiểu đây là package)
try:
    from src.preprocessor import DataPreprocessor
    from src.segmenter import DataSegmenter
    from src.topic_classifier import TopicClassifier
    from src.scorer import SentimentScorer
except ModuleNotFoundError:
    # Fallback cho trường hợp chạy trực tiếp file này mà không qua module context
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.preprocessor import DataPreprocessor
    from src.segmenter import DataSegmenter
    from src.topic_classifier import TopicClassifier
    from src.scorer import SentimentScorer

class SentimentPipeline:
    def __init__(self, resource_path='resources'):
        """
        Khởi tạo dây chuyền: Tuyển dụng 4 công nhân và phát công cụ (Dictionary/Config)
        """
        print("⚙️  Đang khởi động Sentiment Pipeline...")
        self.dict_path = f"{resource_path}/dictionaries"
        self.config_path = resource_path
        
        # 1. Công nhân Làm sạch (Giai đoạn 2)
        self.preprocessor = DataPreprocessor(dict_path=self.dict_path)
        
        # 2. Công nhân Cắt câu (Giai đoạn 3.1)
        self.segmenter = DataSegmenter(dict_path=self.dict_path)
        
        # 3. Công nhân Phân loại Chủ đề (Giai đoạn 3.2)
        self.classifier = TopicClassifier(dict_path=self.dict_path)
        
        # 4. Công nhân Chấm điểm (Giai đoạn 3.3)
        self.scorer = SentimentScorer(resource_path=self.config_path)
        
        print("✅ Hệ thống đã sẵn sàng!")

    def process_file(self, input_path, output_path):
        """
        Hàm chạy toàn bộ quy trình từ A-Z
        """
        # --- BƯỚC 0: KIỂM TRA ĐẦU VÀO ---
        if not os.path.exists(input_path):
            print(f"❌ Lỗi: Không tìm thấy file đầu vào tại {input_path}")
            return None

        try:
            print(f"\n🚀 BẮT ĐẦU XỬ LÝ FILE: {input_path}")
            
            # Đọc dữ liệu thô
            df = pd.read_csv(input_path, encoding='utf-8-sig')
            print(f"📂 Đã nạp {len(df)} dòng dữ liệu thô.")

            # --- BƯỚC 1: LÀM SẠCH (PREPROCESSING) ---
            # Input: Raw Text -> Output: Processed Text, Masked Info
            df_clean = self.preprocessor.run(df)

            # --- BƯỚC 2: TÁCH CÂU (SEGMENTATION) ---
            # Input: 1 dòng -> Output: N dòng (nếu có từ 'nhưng')
            df_segmented = self.segmenter.run(df_clean)

            # --- BƯỚC 3: PHÂN LOẠI CHỦ ĐỀ (TOPIC) ---
            # Input: Segment Content -> Output: Topic Code
            df_classified = self.classifier.run(df_segmented)

            # --- BƯỚC 4: CHẤM ĐIỂM & LOGIC MÂU THUẪN (SCORING) ---
            # Input: Text + Reaction -> Output: Score, Label, Priority
            df_final = self.scorer.run(df_classified)

            # --- BƯỚC 5: LƯU KẾT QUẢ ---
            # Tạo thư mục output nếu chưa có
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Chọn các cột quan trọng để xuất (cho file gọn nhẹ hơn)
            # Hoặc xuất tất cả (df_final) nếu muốn debug
            output_columns = [
                'record_id', 'segment_id', 'social_user_id', 'timestamp',
                'segment_content', 'topic_code', 'reaction_label',
                'text_score', 'reaction_score', 'final_score', 
                'sentiment_label', 'priority_level', 'is_split', 'source_channel'
            ]
            
            # Chỉ giữ lại các cột có trong DataFrame (phòng trường hợp lỗi tên cột)
            final_cols = [c for c in output_columns if c in df_final.columns]
            
            df_final[final_cols].to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ QUY TRÌNH HOÀN TẤT THÀNH CÔNG!")
            print(f"💾 Kết quả cuối cùng lưu tại: {output_path}")
            print("-" * 50)
            
            return df_final

        except Exception as e:
            print(f"\n❌ CÓ LỖI XẢY RA TRONG PIPELINE: {e}")
            import traceback
            traceback.print_exc()
            return None

# --- MAIN ENTRY POINT (Chạy trực tiếp file này) ---
if __name__ == "__main__":
    # Cấu hình đường dẫn
    INPUT_FILE = 'data/raw/raw_comments.csv'
    OUTPUT_FILE = 'data/output/SCORED_FEEDBACK_FINAL.csv'
    
    # Khởi tạo Pipeline
    pipeline = SentimentPipeline(resource_path='resources')
    
    # Chạy
    pipeline.process_file(INPUT_FILE, OUTPUT_FILE)