"""Regex Tokenizer - v3.1

高性能文本分块器，基于正则表达式命名捕获组，
支持 CJK 友好 token 计数、多线程并行、超时保护、embedding-ready 输出。
"""

from .regex_tokenizer import TextChunker, count_tokens
from .processor import TextProcessor
from .api import chunk_text, chunk_file, quick_stats
from .exceptions import (
    TokenizerError,
    ConfigError,
    PatternError,
    ExportError,
    TimeoutError,
)

__version__ = "3.1.0"
__all__ = [
    "TextChunker",
    "count_tokens",
    "TextProcessor",
    "chunk_text",
    "chunk_file",
    "quick_stats",
    "TokenizerError",
    "ConfigError",
    "PatternError",
    "ExportError",
    "TimeoutError",
]
