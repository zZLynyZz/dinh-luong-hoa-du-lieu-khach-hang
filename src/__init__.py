# Khai báo phiên bản
__version__ = "1.0.0"
__author__ = "Lyny"

# Import các class chính ra "mặt tiền" để dễ gọi
from .preprocessor import DataPreprocessor
from .segmenter import DataSegmenter
from .topic_classifier import TopicClassifier
from .scorer import SentimentScorer
from .pipeline import SentimentPipeline