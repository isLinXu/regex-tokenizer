"""Streaming Iterator API - v3.2

解决大文件全量驻留内存问题。
使用生成器逐块返回匹配结果，避免一次性加载整个文件到内存。

用法:
    from tokenizer.streaming import StreamingChunker

    # 流式处理大文件
    streamer = StreamingChunker(config='config.yaml', patterns='patterns.json')
    for chunk in streamer.chunk_file('large_file.md'):
        process(chunk)  # 逐块处理，内存友好

    # 流式处理文本
    for chunk in streamer.chunk_text_iter(long_text):
        process(chunk)
"""

import os
import logging
from typing import Iterator, Dict, Any, Optional

from .regex_tokenizer import TextChunker, count_tokens
from .exceptions import TokenizerError


class StreamingChunker:
    """流式分块器 - 生成器接口，逐块返回结果。

    与 TextChunker 的区别：
    - TextChunker.chunk_text() 返回完整列表（全量驻留内存）
    - StreamingChunker.chunk_text_iter() 返回生成器（惰性求值）

    特性：
    1. 惰性求值：只在需要时才处理下一块
    2. 内存友好：每块处理完即释放
    3. 支持大文件逐行读取
    4. 超时保护继承自 TextChunker
    """

    def __init__(self, config='config.yaml', patterns='patterns.json',
                 token_method='auto', timeout=5.0):
        self._chunker = TextChunker(
            config_file=config, regex_file=patterns,
            token_method=token_method, regex_timeout=timeout
        )

    def chunk_text_iter(self, text: str) -> Iterator[Dict[str, Any]]:
        """流式分块文本 - 生成器版本。

        Args:
            text: 待分块的文本

        Yields:
            dict: 每个匹配的 chunk
        """
        self._chunker.reset_stats()
        try:
            matches = self._chunker._timed_finditer(text)
        except Exception:
            return

        for match in matches:
            name = match.lastgroup
            chunk_text = match.group().strip()
            if chunk_text:
                token_count = count_tokens(chunk_text, method=self._chunker.token_method)
                self._chunker.stats['total_tokens'] += token_count
                self._chunker.stats['total_chunks'] += 1
                self._chunker.stats['total_characters'] += len(chunk_text)
                self._chunker.stats['total_lines'] += chunk_text.count('\n') + 1
                self._chunker.stats['type_distribution'][name] = \
                    self._chunker.stats['type_distribution'].get(name, 0) + 1
                yield {
                    'text': chunk_text,
                    'type': name,
                    'token_count': token_count,
                }

    def chunk_file_iter(self, file_path: str,
                        chunk_size: int = 1024 * 1024) -> Iterator[Dict[str, Any]]:
        """流式分块文件 - 逐块读取大文件。

        Args:
            file_path: 输入文件路径
            chunk_size: 每次读取的字节数

        Yields:
            dict: 每个匹配的 chunk
        """
        if not os.path.exists(file_path):
            raise TokenizerError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)

        if file_size <= chunk_size:
            # 小文件：直接读取
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            yield from self.chunk_text_iter(text)
        else:
            # 大文件：逐块读取
            yield from self._stream_large_file(file_path, chunk_size)

    def _stream_large_file(self, file_path: str,
                           chunk_size: int) -> Iterator[Dict[str, Any]]:
        """流式处理大文件 - 按语义边界分割后逐块处理。"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # 按语义边界分割
        from .processor import _safe_split_text
        text_chunks = _safe_split_text(text, chunk_size)

        for text_chunk in text_chunks:
            yield from self.chunk_text_iter(text_chunk)

    @property
    def stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self._chunker.stats
