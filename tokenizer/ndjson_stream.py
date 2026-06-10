"""Stdout NDJSON 流式输出 - v3.2

DevOps 管道串联：每行输出一个 JSON 对象，便于后续处理。
兼容 jq / yq / grep 等命令行工具。

用法:
    from tokenizer.ndjson_stream import NDJSONWriter

    # 流式输出到 stdout
    writer = NDJSONWriter()
    for chunk in chunks:
        writer.write(chunk)
    writer.close()

    # 流式输出到文件
    writer = NDJSONWriter(output_file='result.ndjson')
    for chunk in chunks:
        writer.write(chunk)
    writer.close()

    # 从 stdin 读取 NDJSON
    reader = NDJSONReader()
    for record in reader.read_stdin():
        process(record)
"""

import sys
import json
import logging
from typing import Dict, Any, Iterator, Optional, TextIO


class NDJSONWriter:
    """NDJSON 流式输出器

    特性：
    1. 行分隔：每行独立 JSON 对象
    2. 缓冲写入：累积到一定量后刷新
    3. 兼容 jq/yq 等工具
    4. 支持管道重定向
    """

    def __init__(self, output_file: Optional[str] = None, buffer_size=100):
        self.buffer_size = buffer_size
        self._buffer = []
        self._output_file = output_file
        self._fh: Optional[TextIO] = None

        if output_file:
            self._fh = open(output_file, 'w', encoding='utf-8')

    def write(self, chunk: Dict[str, Any]):
        """写入一个 JSON 对象"""
        self._buffer.append(chunk)
        if len(self._buffer) >= self.buffer_size:
            self._flush()

    def _flush(self):
        """将缓冲区内容写入输出"""
        target = self._fh if self._fh else sys.stdout
        for item in self._buffer:
            target.write(json.dumps(item, ensure_ascii=False) + '\n')
        target.flush()
        self._buffer.clear()

    def close(self):
        """刷新剩余缓冲区并关闭文件"""
        if self._buffer:
            self._flush()
        if self._fh:
            self._fh.close()
            self._fh = None


class NDJSONReader:
    """NDJSON 流式读取器

    从文件或 stdin 逐行读取 NDJSON 数据。
    """

    def __init__(self, input_file: Optional[str] = None):
        self._input_file = input_file

    def read_stdin(self) -> Iterator[Dict[str, Any]]:
        """从 stdin 逐行读取 NDJSON"""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logging.warning(f"Skipping malformed NDJSON line: {line[:100]}")

    def read_file(self, file_path: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """从文件逐行读取 NDJSON"""
        path = file_path or self._input_file
        if not path:
            raise ValueError("No input file specified")

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    logging.warning(f"Skipping malformed NDJSON line: {line[:100]}")

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        if self._input_file:
            return self.read_file()
        return self.read_stdin()
