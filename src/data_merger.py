import pandas as pd
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) 
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils import ConfigLoader 

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# ==============================================================================
BASE_DIR = project_root 
INPUT_CRAWLER_DIR = os.path.join(BASE_DIR, 'data', 'crawler')
OUTPUT_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')

FILE_POSTS = 'posts_detail.csv'
FILE_COMMENTS = 'comments_detail.csv'
FILE_REACTIONS = 'reactions_detail.csv'
FILE_OUTPUT_MASTER = 'raw_fb_data.csv'

class DataMerger:
    def __init__(self):
        self.posts_path = os.path.join(INPUT_CRAWLER_DIR, FILE_POSTS)
        self.comments_path = os.path.join(INPUT_CRAWLER_DIR, FILE_COMMENTS)
        self.reactions_path = os.path.join(INPUT_CRAWLER_DIR, FILE_REACTIONS)
        self.output_path = os.path.join(OUTPUT_RAW_DIR, FILE_OUTPUT_MASTER)

        # Load ConfigLoader
        self.app_config = ConfigLoader.load()
        self.reaction_map = getattr(self.app_config, 'reaction_map', {})
        if not self.reaction_map:
            print("⚠️ Cảnh báo: Không tìm thấy 'reaction_map' trong ConfigLoader.")

    def load_csv(self, file_path):
        if os.path.exists(file_path):
            try:
                return pd.read_csv(file_path, encoding='utf-8-sig')
            except:
                return pd.DataFrame()
        return pd.DataFrame()

    def normalize_reaction(self, raw_react):
        if pd.isna(raw_react) or raw_react == "":
            return "NONE"
        clean_key = str(raw_react).strip().lower()
        return self.reaction_map.get(clean_key, "NONE")

    def run_merge(self):
        print("🔄 [MERGER] BẮT ĐẦU GHÉP NỐI & CHUẨN HÓA...")
        
        # 1. Đọc dữ liệu
        df_posts = self.load_csv(self.posts_path)
        df_comments = self.load_csv(self.comments_path)
        df_reactions = self.load_csv(self.reactions_path)

        if df_posts.empty:
            print("❌ [MERGER] Thiếu file POSTS.")
            return

        # Xác định Admin để lọc (người đăng bài)
        admin_ids = set(df_posts['user_id'].astype(str).unique())
        print(f"   🛡️ Đã xác định {len(admin_ids)} Admin ID cần lọc.")

        post_context_map = dict(zip(df_posts['post_id'].astype(str), df_posts['context_content']))
        
        merged_records = []
        processed_interactions = set()

        # --- XỬ LÝ COMMENT ---
        if not df_comments.empty:
            skipped_admin = 0
            print(f"   ↳ Đang quét {len(df_comments)} comments...")
            
            for _, row in df_comments.iterrows():
                post_id = str(row.get('post_id', ''))
                user_id = str(row.get('user_id', ''))
                
                # [LỌC ADMIN COMMENT]
                if user_id in admin_ids:
                    skipped_admin += 1
                    continue 

                raw_reaction = "NONE"
                if not df_reactions.empty:
                    react_rows = df_reactions[
                        (df_reactions['post_id'].astype(str) == post_id) & 
                        (df_reactions['user_id'].astype(str) == user_id)
                    ]
                    if not react_rows.empty:
                        raw_reaction = react_rows.iloc[0]['reaction_type']

                # Lấy Timestamp
                cmt_time = row.get('timestamp', row.get('time', None))
                if pd.isna(cmt_time) or cmt_time == "":
                    final_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    final_time = cmt_time

                merged_records.append({
                    'timestamp': final_time,
                    'social_user_id': user_id,
                    'source_channel': 'Fanpage_Comment',
                    'original_text': row.get('original_text', ''),
                    'reaction_label': self.normalize_reaction(raw_reaction),
                    'context_content': None
                })
                processed_interactions.add((post_id, user_id))
            
            if skipped_admin > 0:
                print(f"     🚫 Đã lọc bỏ {skipped_admin} comment của Admin.")

        # --- XỬ LÝ REACTION LẺ ---
        if not df_reactions.empty:
            skipped_admin_react = 0
            print(f"   ↳ Đang quét {len(df_reactions)} reactions lẻ...")
            
            for _, row in df_reactions.iterrows():
                post_id = str(row.get('post_id', ''))
                user_id = str(row.get('user_id', ''))

                # [LỌC ADMIN REACTION]
                if user_id in admin_ids:
                    skipped_admin_react += 1
                    continue

                if (post_id, user_id) not in processed_interactions:
                    context_text = post_context_map.get(post_id, None)
                    if context_text:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        merged_records.append({
                            'timestamp': current_time, 
                            'social_user_id': user_id,
                            'source_channel': 'Fanpage_Post_Reaction',
                            'original_text': None,
                            'reaction_label': self.normalize_reaction(row.get('reaction_type', 'NONE')),
                            'context_content': context_text
                        })
            
            # [MỚI] Thêm dòng này để thông báo số lượng bị lọc
            if skipped_admin_react > 0:
                print(f"     🚫 Đã lọc bỏ {skipped_admin_react} reaction lẻ của Admin.")

        # --- LƯU FILE ---
        if merged_records:
            df_final = pd.DataFrame(merged_records)
            df_final.insert(0, 'record_id', [f"REC_{i+1:03d}" for i in range(len(df_final))])
            
            cols = ['record_id', 'timestamp', 'social_user_id', 'source_channel', 
                    'original_text', 'reaction_label', 'context_content']
            df_final = df_final.reindex(columns=cols)

            os.makedirs(OUTPUT_RAW_DIR, exist_ok=True)
            df_final.to_csv(self.output_path, index=False, encoding='utf-8-sig')
            print(f"✅ [MERGER] Thành công! File: {self.output_path}")
            print(f"📊 Tổng số: {len(df_final)} dòng.")
        else:
            print("⚠️ [MERGER] Không có dữ liệu.")

if __name__ == "__main__":
    merger = DataMerger()
    merger.run_merge()  