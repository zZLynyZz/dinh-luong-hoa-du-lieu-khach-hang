import asyncio
import os
from playwright.async_api import async_playwright

# ==============================================================================
# CẤU HÌNH (CONFIGURATION)
# ==============================================================================
# Tên Profile (Phải khớp với tên trong các file get_posts, get_comments...)
CURRENT_PROFILE_NAME = "acc_clone_1" 

class FacebookLogin:
    def __init__(self):
        """
        Khởi tạo:
        - Xác định vị trí lưu Profile.
        - Lưu ý: os.getcwd() sẽ lấy thư mục hiện tại bạn đang đứng khi chạy lệnh.
        - Nên chạy từ thư mục gốc dự án để Profiles nằm đúng chỗ.
        """
        # Đường dẫn: Dự_án/profiles/acc_clone_1
        self.user_data_dir = os.path.join(os.getcwd(), "profiles", CURRENT_PROFILE_NAME)
        
        # Tạo thư mục nếu chưa có
        os.makedirs(self.user_data_dir, exist_ok=True)

    async def run(self):
        print(f"🚀 [INIT] Đang khởi tạo Profile tại: {self.user_data_dir}")
        print("⚠️ [HƯỚNG DẪN QUAN TRỌNG]:")
        print("   1. Trình duyệt sẽ hiện ra.")
        print("   2. Hãy nhập User/Pass và đăng nhập Facebook thủ công.")
        print("   3. Chọn 'Nhớ mật khẩu' hoặc 'Lưu trình duyệt' nếu được hỏi.")
        print("   4. Khi nào thấy Newsfeed (Trang chủ) hiện ra -> HÃY TẮT TRÌNH DUYỆT.")
        print("   -> Tool sẽ tự động lưu Cookie lại cho các lần sau.")
        
        async with async_playwright() as p:
            # Mở trình duyệt với Profile cố định (Persistent Context)
            # Dữ liệu đăng nhập sẽ được lưu vào thư mục 'profiles'
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False, # Bắt buộc hiện trình duyệt để bạn nhập liệu
                viewport={"width": 1280, "height": 900},
                args=["--disable-notifications"] # Chặn thông báo rác
            )
            page = context.pages[0]
            
            # Truy cập trang chủ Facebook
            print("🌐 Đang truy cập Facebook...")
            await page.goto("https://www.facebook.com/")
            
            # --- VÒNG LẶP CHỜ (WAIT LOOP) ---
            # Treo máy để chờ bạn thao tác thủ công
            # Code sẽ chỉ dừng khi bạn bấm nút X để tắt trình duyệt
            try:
                await page.wait_for_timeout(9999999) 
            except:
                # Khi bạn tắt trình duyệt, Playwright sẽ báo lỗi timeout hoặc connection closed
                # Lúc đó dòng này sẽ được in ra
                print("\n✅ Đã đóng trình duyệt. Cookie và Session đã được lưu an toàn!")

# Chạy chương trình
if __name__ == "__main__":
    bot = FacebookLogin()
    asyncio.run(bot.run())