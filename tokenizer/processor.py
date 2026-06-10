"""文本处理器 - 修复双重处理和数据丢失 Bug

合并双路径为单一路径，使用追加模式写入大文件。
支持多线程并行处理大文件分块。
"""

import logging
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

from .result_saver import save_results, save_stats
from .performance_measurer import measure_performance, format_bytes


class TextProcessor:
    """文本处理器，统一处理大小文件"""

    def __init__(self, chunker, output_file='output.jsonl', stats_file='stats.json',
                 num_threads=1):
        self.chunker = chunker
        self.output_file = output_file
        self.stats_file = stats_file
        self.num_threads = num_threads

    def process_file(self, file_path):
        """处理文件 - 单次处理路径"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        chunks = self.chunker.chunk_text(text)
        self.save_results(chunks)
        self.save_stats()

    def process_large_file(self, file_path, chunk_size=1024 * 1024):
        """处理大文件 - 使用语义边界分割，支持多线程并行"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        text_chunks = _safe_split_text(text, chunk_size)

        if self.num_threads > 1 and len(text_chunks) > 1:
            all_chunks = self._parallel_chunk(text_chunks)
        else:
            all_chunks = []
            for text_chunk in text_chunks:
                chunks = self.chunker.chunk_text(text_chunk)
                all_chunks.extend(chunks)

        # 一次性写入所有结果
        save_results(all_chunks, self.output_file)
        save_stats(self.chunker.stats, self.stats_file)

    def _parallel_chunk(self, text_chunks):
        """多线程并行处理文本分块"""
        # 每个 worker 需要独立的 stats 以避免竞争
        all_chunks = []
        worker_stats_list = []

        def _worker(idx, text_chunk):
            """独立 worker：每个线程创建独立的 chunker 实例"""
            from .regex_tokenizer import TextChunker
            local_chunker = TextChunker.__new__(TextChunker)
            local_chunker.config = self.chunker.config
            local_chunker.regex_patterns = self.chunker.regex_patterns
            local_chunker.token_method = self.chunker.token_method
            local_chunker.regex_timeout = self.chunker.regex_timeout
            local_chunker.chunk_regex = self.chunker.chunk_regex
            local_chunker.stats = {
                'total_tokens': 0,
                'total_chunks': 0,
                'total_characters': 0,
                'total_lines': 0,
                'type_distribution': {},
                'chunk_details': []
            }
            chunks = local_chunker.chunk_text(text_chunk)
            return idx, chunks, local_chunker.stats

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {
                executor.submit(_worker, i, tc): i
                for i, tc in enumerate(text_chunks)
            }
            results = {}
            for future in as_completed(futures):
                idx, chunks, w_stats = future.result()
                results[idx] = (chunks, w_stats)

        # 按原始顺序合并结果
        for idx in sorted(results.keys()):
            chunks, w_stats = results[idx]
            all_chunks.extend(chunks)
            # 合并统计
            self.chunker.stats['total_tokens'] += w_stats['total_tokens']
            self.chunker.stats['total_chunks'] += w_stats['total_chunks']
            self.chunker.stats['total_characters'] += w_stats['total_characters']
            self.chunker.stats['total_lines'] += w_stats['total_lines']
            for k, v in w_stats['type_distribution'].items():
                self.chunker.stats['type_distribution'][k] = \
                    self.chunker.stats['type_distribution'].get(k, 0) + v
            self.chunker.stats['chunk_details'].extend(w_stats['chunk_details'])

        return all_chunks

    def save_results(self, matches, output_format='jsonl'):
        save_results(matches, self.output_file, output_format)

    def save_stats(self):
        save_stats(self.chunker.stats, self.stats_file)

    def print_results(self, matches, execution_time, memory_used):
        logging.info(f"Total chunks: {self.chunker.stats['total_chunks']}")
        logging.info(f"Total tokens: {self.chunker.stats['total_tokens']}")
        logging.info(f"Total characters: {self.chunker.stats['total_characters']}")
        logging.info(f"Total lines: {self.chunker.stats['total_lines']}")
        logging.info(f"Execution time: {execution_time:.2f} seconds")
        logging.info(f"Memory used: {format_bytes(memory_used)}")

        logging.info('\nFirst 10 chunks:')
        if matches:
            for match in matches[:10]:
                logging.info(repr(match)[:50])
        else:
            logging.info('No chunks found.')

        if execution_time > 5:
            logging.warning('Execution time exceeded 5 seconds.')
        if memory_used > 100 * 1024 * 1024:
            logging.warning('Memory usage exceeded 100 MB.')


def _safe_split_text(text, chunk_size):
    """按语义边界安全分割文本"""
    chunks = []
    start = 0
    while start < len(text):
        # 寻找最近的段落边界（双换行）
        boundary = text.rfind('\n\n', start + chunk_size // 2, start + chunk_size + 200)
        if boundary == -1:
            # 回退到最近的换行
            boundary = text.rfind('\n', start + chunk_size // 2, start + chunk_size + 200)
        if boundary == -1:
            # 回退到最近的空格
            boundary = text.rfind(' ', start + chunk_size // 2, start + chunk_size + 200)
        if boundary == -1 or boundary <= start:
            boundary = start + chunk_size  # 无奈硬切
        chunks.append(text[start:boundary])
        start = boundary
    return chunks
