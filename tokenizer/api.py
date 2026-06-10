"""Regex Tokenizer Python API

提供简洁的编程接口，支持一行代码完成文本分块。

用法:
    from tokenizer.api import chunk_text, chunk_file

    # 分块字符串
    results = chunk_text("# Hello\\nWorld.", config="config.yaml")

    # 分块文件
    stats = chunk_file("input.md", output="output.jsonl")

    # embedding-ready 输出
    stats = chunk_file("input.md", output="out.jsonl", format="embedding")
"""

import os
import logging

from .regex_tokenizer import TextChunker
from .processor import TextProcessor
from .exceptions import TokenizerError


def chunk_text(text, config='config.yaml', patterns='patterns.json',
               token_method='auto', timeout=5.0):
    """对文本字符串进行分块。

    Args:
        text: 待分块的文本
        config: YAML 配置文件路径
        patterns: JSON 正则模式文件路径
        token_method: token 计数方法 ('auto'/'whitespace'/'character')
        timeout: 正则匹配超时秒数

    Returns:
        list[dict]: 分块结果，每项包含 text, type, token_count

    Raises:
        TokenizerError: 配置/模式/超时等错误
    """
    chunker = TextChunker(
        config_file=config, regex_file=patterns,
        token_method=token_method, regex_timeout=timeout
    )
    return chunker.chunk_text(text)


def chunk_file(file_path, output=None, config='config.yaml', patterns='patterns.json',
               format='jsonl', num_threads=1, chunk_size=1048576,
               stats_file=None, token_method='auto', timeout=5.0):
    """对文件进行分块并保存结果。

    Args:
        file_path: 输入文件路径
        output: 输出文件路径（默认: <input>.jsonl）
        config: YAML 配置文件路径
        patterns: JSON 正则模式文件路径
        format: 输出格式 ('jsonl'/'csv'/'xml'/'excel'/'embedding')
        num_threads: 并行线程数
        chunk_size: 大文件分块大小（字节）
        stats_file: 统计文件路径（默认: <output>.stats.json）
        token_method: token 计数方法
        timeout: 正则匹配超时秒数

    Returns:
        dict: 统计信息（total_chunks, total_tokens, type_distribution 等）

    Raises:
        TokenizerError: 配置/模式/超时等错误
        ExportError: 导出失败
        FileNotFoundError: 输入文件不存在
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if output is None:
        base, _ = os.path.splitext(file_path)
        output = f"{base}.jsonl"

    if stats_file is None:
        stats_file = output.replace('.jsonl', '.stats.json')

    chunker = TextChunker(
        config_file=config, regex_file=patterns,
        token_method=token_method, regex_timeout=timeout
    )
    processor = TextProcessor(
        chunker, output_file=output, stats_file=stats_file,
        num_threads=num_threads
    )

    if os.path.getsize(file_path) > chunk_size:
        processor.process_large_file(file_path, chunk_size=chunk_size)
    else:
        processor.process_file(file_path)

    return chunker.stats


def quick_stats(text, config='config.yaml', patterns='patterns.json'):
    """快速获取文本分块统计（不保存文件）。

    Args:
        text: 待分析的文本
        config: YAML 配置文件路径
        patterns: JSON 正则模式文件路径

    Returns:
        dict: 统计摘要
    """
    chunker = TextChunker(config_file=config, regex_file=patterns)
    chunker.chunk_text(text)
    return {
        'total_chunks': chunker.stats['total_chunks'],
        'total_tokens': chunker.stats['total_tokens'],
        'total_characters': chunker.stats['total_characters'],
        'total_lines': chunker.stats['total_lines'],
        'type_distribution': chunker.stats['type_distribution'],
    }
