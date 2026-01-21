import argparse
import os
import sys
from src import SentimentPipeline  # Import ngắn gọn nhờ đã sửa __init__.py

def main():
    # 1. Cấu hình bộ đọc tham số (Argument Parser)
    # Giúp bạn có thể chạy lệnh kiểu: python main.py --input data/new_file.csv
    parser = argparse.ArgumentParser(description="Tikop Sentiment Analysis Engine")
    
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/raw/raw_comments.csv',
        help='Đường dẫn đến file dữ liệu thô (CSV)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/output/SCORED_FEEDBACK_FINAL.csv',
        help='Đường dẫn để lưu file kết quả'
    )
    
    args = parser.parse_args()

    # 2. Kiểm tra tài nguyên
    if not os.path.exists('resources/config.yaml'):
        print("❌ Lỗi: Không tìm thấy thư mục 'resources'. Hãy đảm bảo bạn đang chạy lệnh tại thư mục gốc của dự án.")
        sys.exit(1)

    print("="*50)
    print(f"🚀 KHỞI ĐỘNG HỆ THỐNG ĐỊNH LƯỢNG THÁI ĐỘ KHÁCH HÀNG")
    print(f"📂 Input:  {args.input}")
    print(f"💾 Output: {args.output}")
    print("="*50)

    # 3. Khởi tạo Pipeline
    try:
        # Pipeline tự động load config từ folder resources
        pipeline = SentimentPipeline(resource_path='resources')
        
        # 4. Chạy xử lý
        result_df = pipeline.process_file(args.input, args.output)
        
        if result_df is not None:
            print("\n" + "="*50)
            print("🎉 CHƯƠNG TRÌNH HOÀN TẤT THÀNH CÔNG!")
            print(f"Tổng số dòng dữ liệu đã xử lý: {len(result_df)}")
            print("="*50)
        else:
            print("\n❌ Chương trình thất bại. Vui lòng kiểm tra lại log lỗi phía trên.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn tại main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()