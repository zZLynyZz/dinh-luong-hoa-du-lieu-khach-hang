
import asyncio

from src.crawler import (
    FacebookPostCrawler, 
    FacebookCommentCrawler, 
    FacebookReactionCrawler
)

class CrawlerManager:
    def __init__(self, target_url, max_posts):
        self.target_url = target_url
        self.max_posts = max_posts

    async def run_full_crawl(self):
        print("🤖 [MANAGER] BẮT ĐẦU QUY TRÌNH CRAWL DATA...")

        # 1. CRAWL POSTS
        print("\n=== GIAI ĐOẠN 1: CRAWL POSTS ===")
        post_bot = FacebookPostCrawler(target_url=self.target_url, max_posts=self.max_posts)
        await post_bot.run()

        # 2. CRAWL COMMENTS
        print("\n=== GIAI ĐOẠN 2: CRAWL COMMENTS ===")
        comment_bot = FacebookCommentCrawler()
        await comment_bot.run()

        # 3. CRAWL REACTIONS
        print("\n=== GIAI ĐOẠN 3: CRAWL REACTIONS ===")
        reaction_bot = FacebookReactionCrawler()
        await reaction_bot.run()

        print("\n✅ [MANAGER] ĐÃ HOÀN THÀNH TOÀN BỘ!")