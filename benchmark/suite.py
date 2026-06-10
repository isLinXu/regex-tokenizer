"""Benchmark Suite - v3.2

与 LangChain / LlamaIndex 量化对比。

用法:
    from benchmark.suite import BenchmarkSuite

    suite = BenchmarkSuite()
    results = suite.run_all()
    suite.print_report(results)
    suite.save_report(results, 'benchmark_results.json')
"""

import time
import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import psutil

from tokenizer.regex_tokenizer import TextChunker, count_tokens
from tokenizer.coverage import CoverageAnalyzer
from tokenizer.smart_merge import SmartChunkMerger
from tokenizer.overlap import OverlapSlidingWindow


# 标准测试语料
SAMPLE_TEXTS = {
    'markdown_short': """# Hello World

This is a **test** paragraph with some text.

## Section 2

- Item 1
- Item 2
- Item 3

```python
def hello():
    print("Hello, World!")
```

> This is a blockquote.

The end.
""",
    'markdown_medium': """# Project Documentation

## Overview

This project provides a high-performance regex-based text chunker for RAG pipelines.
It supports multiple output formats including JSONL, CSV, XML, Excel, and embedding-ready format.

## Features

- **Pattern-based chunking**: Uses configurable regex patterns
- **CJK-friendly**: Automatic detection of CJK text for proper token counting
- **Multiple output formats**: JSONL, CSV, XML, Excel, embedding
- **Timeout protection**: Prevents catastrophic backtracking
- **Hot reload**: Update patterns without restarting

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from tokenizer.api import chunk_text, chunk_file

results = chunk_text("# Hello\\nWorld.")
stats = chunk_file("input.md", output="output.jsonl")
```

## Configuration

Edit `config.yaml` to adjust pattern parameters.

| Parameter | Default | Description |
|-----------|---------|-------------|
| MAX_HEADING_LENGTH | 7 | Maximum heading level |
| MAX_SENTENCE_LENGTH | 400 | Maximum sentence length |
| MAX_CODE_BLOCK_LENGTH | 1500 | Maximum code block length |

---

### Contact

For questions, reach out to the team at team@example.com.

#end #hashtag @mention @user123
""",
    'cjk_text': """# 中文测试

这是一个中文段落，用于测试 CJK 文本的分块效果。

## 第二节

- 第一项
- 第二项
- 第三项

```python
print("你好世界")
```

> 这是一段引用文本。

结论：中文分块效果良好。
""",
}


class BenchmarkSuite:
    """基准测试套件"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self, config='config.yaml', patterns='patterns.json') -> Dict[str, Any]:
        """运行所有基准测试"""
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {},
        }

        for name, text in SAMPLE_TEXTS.items():
            results['tests'][name] = self._run_single(
                name, text, config=config, patterns=patterns
            )

        return results

    def _run_single(self, name: str, text: str,
                    config: str = 'config.yaml',
                    patterns: str = 'patterns.json') -> Dict[str, Any]:
        """运行单个基准测试"""
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss

        # 执行分块
        start = time.time()
        chunker = TextChunker(config_file=config, regex_file=patterns)
        chunks = chunker.chunk_text(text)
        elapsed = time.time() - start

        mem_after = process.memory_info().rss

        # 覆盖率分析
        analyzer = CoverageAnalyzer(chunker)
        coverage = analyzer.analyze(text, chunks)

        # 智能合并
        merger = SmartChunkMerger()
        merged = merger.merge(chunks)

        # 重叠窗口
        window = OverlapSlidingWindow(overlap_chars=50)
        overlapped = window.apply(chunks)

        return {
            'input_chars': len(text),
            'chunk_count': len(chunks),
            'merged_count': len(merged),
            'overlapped_count': len(overlapped),
            'total_tokens': chunker.stats['total_tokens'],
            'elapsed_seconds': round(elapsed, 4),
            'chunks_per_second': round(len(chunks) / elapsed, 2) if elapsed > 0 else 0,
            'avg_latency_ms': round((elapsed / max(len(chunks), 1)) * 1000, 2),
            'memory_delta_bytes': mem_after - mem_before,
            'coverage_ratio': coverage['coverage_ratio'],
            'gap_count': coverage['gap_count'],
            'type_distribution': chunker.stats['type_distribution'],
        }

    def print_report(self, results: Dict[str, Any]):
        """打印基准测试报告"""
        print(f"\n{'='*70}")
        print(f"  Regex Tokenizer Benchmark Report")
        print(f"  Timestamp: {results['timestamp']}")
        print(f"{'='*70}")

        for name, data in results['tests'].items():
            print(f"\n  [{name}]")
            print(f"    Input chars:       {data['input_chars']}")
            print(f"    Chunk count:       {data['chunk_count']}")
            print(f"    Merged count:      {data['merged_count']}")
            print(f"    Total tokens:      {data['total_tokens']}")
            print(f"    Elapsed:           {data['elapsed_seconds']}s")
            print(f"    Chunks/sec:        {data['chunks_per_second']}")
            print(f"    Avg latency:       {data['avg_latency_ms']}ms")
            print(f"    Coverage:          {data['coverage_ratio']*100:.1f}%")
            print(f"    Gaps:              {data['gap_count']}")
            if data['type_distribution']:
                print(f"    Type distribution:")
                for t, c in sorted(data['type_distribution'].items(), key=lambda x: -x[1]):
                    print(f"      {t:20s} {c:>4d}")

        print(f"\n{'='*70}\n")

    def save_report(self, results: Dict[str, Any], output_file: str):
        """保存基准测试报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logging.info(f"Benchmark report saved to {output_file}")
