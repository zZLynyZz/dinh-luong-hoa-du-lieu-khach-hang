import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CẤU HÌNH TRANG (Phải để đầu tiên)
st.set_page_config(
    page_title="Tikop Sentiment Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. HÀM LOAD DỮ LIỆU
@st.cache_data
def load_data():
    # Thử các đường dẫn có thể xảy ra
    possible_paths = [
        'data/output/SCORED_FEEDBACK_FINAL.csv', # Chạy từ thư mục gốc
        '../data/output/SCORED_FEEDBACK_FINAL.csv', # Chạy từ thư mục src
        'SCORED_FEEDBACK_FINAL.csv' # File để cùng chỗ
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    if file_path is None:
        return None
    
    df = pd.read_csv(file_path)
    # Xử lý thời gian
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    return df

# Load data
df = load_data()

# 3. KIỂM TRA DỮ LIỆU ĐẦU VÀO
if df is None:
    st.error("❌ LỖI: Không tìm thấy file 'SCORED_FEEDBACK_FINAL.csv'.")
    st.warning("👉 Hãy chắc chắn bạn đã chạy lệnh: `python main.py` trước.")
    st.info(f"Đường dẫn hiện tại của hệ thống: {os.getcwd()}")
else:
    # --- SIDEBAR (BỘ LỌC) ---
    st.sidebar.header("🔍 Bộ lọc dữ liệu")
    
    # Kiểm tra cột có tồn tại không trước khi tạo bộ lọc
    if 'topic_code' in df.columns:
        all_topics = ['All'] + list(df['topic_code'].astype(str).unique())
        selected_topic = st.sidebar.selectbox("Chọn Chủ đề:", all_topics)
    else:
        selected_topic = 'All'
        
    if 'priority_level' in df.columns:
        all_priorities = ['All'] + list(df['priority_level'].astype(str).unique())
        selected_priority = st.sidebar.selectbox("Mức độ ưu tiên:", all_priorities)
    else:
        selected_priority = 'All'

    # Áp dụng lọc
    df_filtered = df.copy()
    if selected_topic != 'All':
        df_filtered = df_filtered[df_filtered['topic_code'] == selected_topic]
    if selected_priority != 'All':
        df_filtered = df_filtered[df_filtered['priority_level'] == selected_priority]

    # --- HEADER ---
    st.title("📊 Dashboard Phân Tích Cảm Xúc Khách Hàng")
    st.markdown("---")

    # --- SECTION 1: KPI TỔNG QUAN ---
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        total_feedback = len(df_filtered)
        
        # Xử lý trường hợp cột final_score bị lỗi hoặc rỗng
        avg_score = 0
        if 'final_score' in df_filtered.columns:
            avg_score = df_filtered['final_score'].mean()
            
        critical_count = 0
        if 'priority_level' in df_filtered.columns:
            critical_count = len(df_filtered[df_filtered['priority_level'] == 'CRITICAL'])
        
        neg_rate = 0
        if 'final_score' in df_filtered.columns and total_feedback > 0:
            neg_count = len(df_filtered[df_filtered['final_score'] < 0])
            neg_rate = (neg_count / total_feedback * 100)

        col1.metric("Tổng Phản hồi", f"{total_feedback:,}")
        col2.metric("Điểm Hài lòng (TB)", f"{avg_score:.2f}")
        col3.metric("Vấn đề Nghiêm trọng", f"{critical_count}", delta="-Critical" if critical_count > 0 else "off")
        col4.metric("Tỷ lệ Tiêu cực", f"{neg_rate:.1f}%")

    except Exception as e:
        st.error(f"Lỗi hiển thị KPI: {e}")

    st.markdown("---")

    # --- SECTION 2: BIỂU ĐỒ ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🎭 Phân bố Cảm xúc")
        try:
            if 'sentiment_label' in df_filtered.columns:
                # Đếm số lượng trước khi vẽ (Fix lỗi values='record_id' cũ)
                sentiment_counts = df_filtered['sentiment_label'].value_counts().reset_index()
                sentiment_counts.columns = ['sentiment_label', 'count']
                
                fig_pie = px.pie(
                    sentiment_counts, 
                    names='sentiment_label', 
                    values='count',
                    color='sentiment_label',
                    color_discrete_map={
                        'PANIC': '#ff2b2b', 'NEGATIVE': '#ff9f43', 
                        'SKEPTICAL': '#feca57', 'NEUTRAL': '#c8d6e5',
                        'POSITIVE': '#1dd1a1', 'ADVOCACY': '#5f27cd'
                    },
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("Không tìm thấy cột 'sentiment_label'")
        except Exception as e:
            st.error(f"Lỗi vẽ biểu đồ tròn: {e}")

    with c2:
        st.subheader("🔥 Điểm nóng theo Chủ đề")
        try:
            if 'topic_code' in df_filtered.columns and 'final_score' in df_filtered.columns:
                topic_stats = df_filtered.groupby('topic_code')['final_score'].mean().reset_index()
                topic_stats = topic_stats.sort_values('final_score')
                
                fig_bar = px.bar(
                    topic_stats, 
                    x='final_score', 
                    y='topic_code',
                    orientation='h',
                    color='final_score',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    range_color=[-2, 2],
                    text_auto='.2f'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"Lỗi vẽ biểu đồ cột: {e}")

    # --- SECTION 3: DANH SÁCH CHI TIẾT ---
    st.subheader("🚨 Danh sách cần xử lý gấp")
    if 'priority_level' in df_filtered.columns:
        urgent_df = df_filtered[df_filtered['priority_level'].isin(['CRITICAL', 'HIGH'])].sort_values('final_score')
        
        if not urgent_df.empty:
            # Chọn cột tồn tại để hiện
            cols_to_show = ['segment_content', 'topic_code', 'final_score', 'sentiment_label']
            valid_cols = [c for c in cols_to_show if c in urgent_df.columns]
            
            st.dataframe(urgent_df[valid_cols], use_container_width=True)
        else:
            st.success("Không có vấn đề nghiêm trọng.")