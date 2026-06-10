"""Regex Tokenizer - v3.2

高性能文本分块器，基于正则表达式命名捕获组，
支持 CJK 友好 token 计数、多线程并行、超时保护、embedding-ready 输出。

v3.2 新增：
- Coverage 分析 & Gap 检测
- Overlap 滑动窗口
- Streaming Iterator API
- Smart Chunk Merge
- Stdout NDJSON 流式输出
- Benchmark 套件
"""

from .regex_tokenizer import TextChunker, count_tokens
from .processor import TextProcessor
from .api import chunk_text, chunk_file, quick_stats
from .coverage import CoverageAnalyzer
from .overlap import OverlapSlidingWindow
from .streaming import StreamingChunker
from .smart_merge import SmartChunkMerger
from .ndjson_stream import NDJSONWriter, NDJSONReader
from .exceptions import (
    TokenizerError,
    ConfigError,
    PatternError,
    ExportError,
    TimeoutError,
)

__version__ = "3.2.0"
__all__ = [
    "TextChunker",
    "count_tokens",
    "TextProcessor",
    "chunk_text",
    "chunk_file",
    "quick_stats",
    "CoverageAnalyzer",
    "OverlapSlidingWindow",
    "StreamingChunker",
    "SmartChunkMerger",
    "NDJSONWriter",
    "NDJSONReader",
    "TokenizerError",
    "ConfigError",
    "PatternError",
    "ExportError",
    "TimeoutError",
]
