"""Regex Tokenizer - v3.0

高性能文本分块器，基于正则表达式命名捕获组，
支持 CJK 友好 token 计数、多线程并行、超时保护。
"""

from .regex_tokenizer import TextChunker, count_tokens
from .processor import TextProcessor
from .exceptions import (
    TokenizerError,
    ConfigError,
    PatternError,
    ExportError,
    TimeoutError,
)

__version__ = "3.0.0"
__all__ = [
    "TextChunker",
    "count_tokens",
    "TextProcessor",
    "TokenizerError",
    "ConfigError",
    "PatternError",
    "ExportError",
    "TimeoutError",
]
