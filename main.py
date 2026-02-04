import os
import sys
import time
import asyncio # 👈 Thêm thư viện này để chạy Async

# ==============================================================================
# [CẤU HÌNH ĐẦU VÀO] - BẠN CHỈNH SỬA LINK PAGE Ở ĐÂY
# ==============================================================================
TARGET_PAGE_URL = 'https://www.facebook.com/tikopapp' 

# Số lượng bài viết muốn lấy
NUM_POSTS_TO_CRAWL = 10 

# ==============================================================================
# CẤU HÌNH HỆ THỐNG
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import Modules
from src import CrawlerManager, DataMerger, DataProcessor, SentimentScorer

def print_separator(step_name):
    print("\n" + "="*60)
    print(f"🚀 BẮT ĐẦU GIAI ĐOẠN: {step_name.upper()}")
    print("="*60)

def main():

    total_start = time.time()
    print(f"🕒 Engine khởi động lúc: {time.ctime(total_start)}")
    print(f"🎯 Mục tiêu: {TARGET_PAGE_URL} | Số lượng: {NUM_POSTS_TO_CRAWL} bài")

    # --------------------------------------------------------------------------
    # PHASE 1: CRAWLING 
    # --------------------------------------------------------------------------
    # Lưu ý: Nếu bạn đã có dữ liệu sẵn trong data/crawler và không muốn cào lại
    # thì có thể comment (đóng băng) đoạn này lại.
    
    print_separator("1. CRAWLING DATA")
    try:
        # 1. Truyền tham số ngay lúc khởi tạo class
        crawler = CrawlerManager(target_url=TARGET_PAGE_URL, max_posts=NUM_POSTS_TO_CRAWL)
        
        # 2. Dùng asyncio.run() vì hàm run_full_crawl là async
        asyncio.run(crawler.run_full_crawl())
            
    except Exception as e:
        print(f"⚠️ Bỏ qua bước Crawler hoặc có lỗi: {e}")
        print("👉 Tiếp tục xử lý dữ liệu đang có sẵn trong data/crawler...")

    # --------------------------------------------------------------------------
    # PHASE 2: MERGING
    # --------------------------------------------------------------------------
    print_separator("2. MERGING RAW DATA")
    try:
        merger = DataMerger()
        merger.run_merge()
    except Exception as e:
        print(f"❌ Lỗi bước Merge: {e}")
        return 

    # --------------------------------------------------------------------------
    # PHASE 3: PROCESSING
    # --------------------------------------------------------------------------
    print_separator("3. PROCESSING DATA")
    try:
        processor = DataProcessor()
        processor.run_process()
    except Exception as e:
        print(f"❌ Lỗi bước Processing: {e}")
        return

    # --------------------------------------------------------------------------
    # PHASE 4: SCORING
    # --------------------------------------------------------------------------
    print_separator("4. SENTIMENT SCORING")
    try:
        scorer = SentimentScorer()
        scorer.run_analysis()
    except Exception as e:
        print(f"❌ Lỗi bước Scoring: {e}")
        return

    # --------------------------------------------------------------------------
    # KẾT THÚC
    # --------------------------------------------------------------------------
    total_end = time.time()
    duration = total_end - total_start
    print("\n" + "="*60)
    print(f"✅ HOÀN TẤT TOÀN BỘ QUY TRÌNH!")
    print(f"⏱️ Tổng thời gian: {duration:.2f} giây")
    print("="*60)
    print("📂 Xem báo cáo tại: data/reports/final_sentiment_report.csv")

if __name__ == "__main__":
    main()