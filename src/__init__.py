# src/__init__.py

# 1. Module Crawler
from .run_crawler import CrawlerManager

# 2. Module Merger
from .data_merger import DataMerger

# 3. Module Processing (Làm sạch)
from .data_processor import DataProcessor

# 4. Module Analysis (Chấm điểm & Phân loại)
from .sentiment_scorer import SentimentScorer
