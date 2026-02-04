# 📊 Tikop Sentiment Engine

Hệ thống tự động thu thập, xử lý và phân tích cảm xúc khách hàng từ dữ liệu mạng xã hội (Facebook), tập trung vào phân tích phản hồi về sản phẩm Fintech (Tikop).

---

## 🚀 Tính năng chính

Hệ thống hoạt động theo quy trình Pipeline 4 bước khép kín + 1 Dashboard hiển thị:

1.  **🕷️ Crawling (Thu thập):**
    * Module chuyên biệt: `src/crawler` tách lẻ nhiệm vụ (Posts, Comments, Reactions).
    * Tự động đăng nhập Facebook (`login_fb.py`) và lưu Cookie.
    * Hỗ trợ chạy đa luồng (Async) tăng tốc độ.
2.  **🔄 Merging (Gộp & Lọc thô):**
    * Gộp dữ liệu rời rạc từ `data/crawler` thành một file Master.
    * **Lọc Admin:** Loại bỏ tương tác của chính Fanpage.
    * **Mapping:** Chuẩn hóa icon cảm xúc.
3.  **🧹 Processing (Làm sạch):**
    * **Masking PII:** Che thông tin nhạy cảm (SĐT, STK, Email).
    * **Re-indexing:** Đánh lại mã ID chuẩn (`REC_001`...) cho toàn bộ dữ liệu.
4.  **🧠 Scoring (Chấm điểm & Phân loại):**
    * **Segmentation:** Tách câu ghép (VD: `SEG_001_A`, `SEG_001_B`).
    * **Context-aware:** Hiểu ngữ cảnh khi khách chỉ thả Reaction.
    * **Ranking:** Xếp hạng mức độ nghiêm trọng (`CRITICAL`, `HIGH`).
5.  **📈 Dashboard:** Giao diện trực quan hóa dữ liệu báo cáo.

---

## 📂 Cấu trúc dự án

Dựa trên cấu trúc thư mục thực tế:

```text
TIKOP_SENTIMENT_ENGINE/
├── data/                   # KHO DỮ LIỆU
│   ├── crawler/            # Output thô từ module Crawler (csv từng phần)
│   ├── raw/                # Output từ Merger (raw_fb_data.csv)
│   ├── processed/          # Output từ Processor (processed_data.csv)
│   ├── reports/            # Báo cáo cuối cùng (final_sentiment_report.csv)
│   └── profiles/           # (Lưu trữ profile người dùng - Mở rộng)
├── resources/              # TÀI NGUYÊN
│   ├── config.yaml         # Cấu hình hệ thống (trọng số, ngưỡng điểm)
│   └── dictionaries/       # Các bộ từ điển (keywords, teencode...)
├── src/                    # SOURCE CODE CHÍNH
│   ├── crawler/            # Module Crawl chi tiết
│   │   ├── get_posts.py    # Cào bài viết
│   │   ├── get_comments.py # Cào bình luận
│   │   ├── get_reactions.py# Cào reaction
│   │   └── login_fb.py     # Xử lý đăng nhập
│   ├── utils/              # Tiện ích chung
│   ├── data_merger.py      # Logic gộp và lọc dữ liệu
│   ├── data_processor.py   # Logic làm sạch và chuẩn hóa
│   ├── run_crawler.py      # Script điều phối Crawler
│   └── sentiment_scorer.py # Logic chấm điểm cảm xúc
├── tests/                  # Thư mục kiểm thử (Unit test)
├── .gitignore              # File cấu hình git bỏ qua
├── dashboard.py            # Giao diện hiển thị báo cáo (Streamlit/Dash)
├── main.py                 # "Nhạc trưởng" điều phối toàn bộ luồng chạy
├── README.md               # Tài liệu hướng dẫn
└── requirements.txt        # Danh sách thư viện cần cài đặt