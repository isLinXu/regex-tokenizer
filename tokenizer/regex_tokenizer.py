"""Regex Tokenizer core module - v3.0

Optimizations:
1. Use regex module instead of re, with timeout protection
2. Use named capture groups instead of fullmatch loop
3. CJK-friendly token counting
4. Correct pattern priority
5. Type distribution statistics
"""

import signal
import threading
import logging

import regex

from .loader import load_config, load_and_substitute_regex_patterns
from .logger_setup import setup_logging
from .exceptions import PatternError, TimeoutError


PATTERN_PRIORITY = [
    "code_block",
    "table",
    "horizontal_rule",
    "headings",
    "list_items",
    "block_quote",
    "latex_style",
    "html_style",
    "citations",
    "email",
    "url",
    "phone",
    "hashtag",
    "mention",
    "ipv4",
    "ipv6",
    "date",
    "time",
    "quoted_text",
    "paragraph",
    "sentence",
    "fallback",
]


def count_tokens(text, method='auto'):
    if method == 'whitespace':
        return len(text.split())
    elif method == 'character':
        return sum(1 for c in text if not c.isspace())
    elif method == 'auto':
        cjk_count = sum(
            1 for c in text
            if '\u4e00' <= c <= '\u9fff'
            or '\u3400' <= c <= '\u4dbf'
            or '\U00020000' <= c <= '\U0002a6df'
            or '\u3040' <= c <= '\u309f'
            or '\u30a0' <= c <= '\u30ff'
            or '\uac00' <= c <= '\ud7af'
        )
        ratio = cjk_count / max(len(text), 1)
        if ratio > 0.3:
            return sum(1 for c in text if not c.isspace())
        else:
            return len(text.split())
    raise ValueError(f"Unknown token count method: {method}")


class TextChunker:
    def __init__(self, config_file='config.yaml', regex_file='patterns.json',
                 token_method='auto', regex_timeout=5.0):
        self.config = load_config(config_file)
        self._regex_file = regex_file
        self.regex_patterns = load_and_substitute_regex_patterns(regex_file, self.config)
        self.token_method = token_method
        self.regex_timeout = regex_timeout
        self.compile_chunk_regex()
        setup_logging()
        self.stats = {
            'total_tokens': 0,
            'total_chunks': 0,
            'total_characters': 0,
            'total_lines': 0,
            'type_distribution': {},
            'chunk_details': []
        }

    def compile_chunk_regex(self):
        self.patterns_dict = self.regex_patterns
        named_patterns = []
        ordered_names = []
        for name in PATTERN_PRIORITY:
            if name in self.regex_patterns:
                ordered_names.append(name)
        for name in self.regex_patterns:
            if name not in ordered_names:
                ordered_names.append(name)
        for name in ordered_names:
            pattern = self.regex_patterns[name]
            named_patterns.append(f"(?P<{name}>{pattern})")
        combined = "|".join(named_patterns)
        try:
            self.chunk_regex = regex.compile(
                combined,
                regex.MULTILINE | regex.UNICODE
            )
        except regex.error as e:
            raise PatternError(f"Failed to compile regex: {e}")

    def chunk_text(self, text):
        chunks = []
        try:
            matches = self._timed_finditer(text)
        except TimeoutError:
            logging.warning("Regex matching timed out, returning partial results")
            return chunks
        for match in matches:
            name = match.lastgroup
            chunk_text = match.group().strip()
            if chunk_text:
                token_count = count_tokens(chunk_text, method=self.token_method)
                self.stats['total_tokens'] += token_count
                self.stats['total_chunks'] += 1
                self.stats['total_characters'] += len(chunk_text)
                self.stats['total_lines'] += chunk_text.count('\n') + 1
                self.stats['type_distribution'][name] = \
                    self.stats['type_distribution'].get(name, 0) + 1
                self.stats['chunk_details'].append({
                    'text': chunk_text,
                    'type': name,
                    'token_count': token_count,
                    'character_count': len(chunk_text),
                    'line_count': chunk_text.count('\n') + 1
                })
                chunks.append({
                    'text': chunk_text,
                    'type': name,
                    'token_count': token_count
                })
        return chunks

    def _timed_finditer(self, text):
        """带超时保护的 finditer。

        优先使用 signal.alarm (Unix)，否则回退到线程超时。
        """
        if hasattr(signal, 'SIGALRM') and threading.current_thread() is threading.main_thread():
            return self._unix_timed_finditer(text)
        return self._thread_timed_finditer(text)

    def _unix_timed_finditer(self, text):
        """Unix 平台使用 SIGALRM 实现超时"""
        result = []
        timed_out = [False]

        def _handler(signum, frame):
            timed_out[0] = True

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(int(self.regex_timeout))
        try:
            for match in self.chunk_regex.finditer(text):
                if timed_out[0]:
                    break
                result.append(match)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        if timed_out[0]:
            raise TimeoutError(
                f"Regex matching exceeded {self.regex_timeout}s timeout"
            )
        return result

    def _thread_timed_finditer(self, text):
        """跨平台：使用线程超时机制"""
        result = []
        exception = [None]

        def _worker():
            try:
                for match in self.chunk_regex.finditer(text):
                    result.append(match)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.regex_timeout)

        if thread.is_alive():
            raise TimeoutError(
                f"Regex matching exceeded {self.regex_timeout}s timeout"
            )

        if exception[0]:
            raise exception[0]

        return result

    def update_regex_patterns(self, new_patterns):
        """热更新：合并新模式并重新编译"""
        self.regex_patterns.update(new_patterns)
        self.compile_chunk_regex()

    def reload_patterns(self, regex_file=None):
        """热更新：从文件重新加载 patterns 并重新编译。

        Args:
            regex_file: 新的 patterns 文件路径（默认使用原路径）
        """
        if regex_file is not None:
            self._regex_file = regex_file
        self.regex_patterns = load_and_substitute_regex_patterns(
            self._regex_file, self.config
        )
        self.compile_chunk_regex()
        logging.info(f"Patterns reloaded from {self._regex_file}")

    def reset_stats(self):
        """重置统计信息（处理新文件前调用）"""
        self.stats = {
            'total_tokens': 0,
            'total_chunks': 0,
            'total_characters': 0,
            'total_lines': 0,
            'type_distribution': {},
            'chunk_details': []
        }
