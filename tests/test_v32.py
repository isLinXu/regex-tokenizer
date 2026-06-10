"""Regex Tokenizer v3.2 单元测试

覆盖：Coverage 分析、Overlap 窗口、Streaming Iterator、
Smart Merge、NDJSON 流式输出、Benchmark 套件。
"""

import os
import json
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tokenizer.regex_tokenizer import TextChunker, count_tokens
from tokenizer.coverage import CoverageAnalyzer
from tokenizer.overlap import OverlapSlidingWindow
from tokenizer.streaming import StreamingChunker
from tokenizer.smart_merge import SmartChunkMerger
from tokenizer.ndjson_stream import NDJSONWriter, NDJSONReader
from tokenizer.exceptions import TokenizerError


# ── fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_config(tmp_dir):
    config_path = os.path.join(tmp_dir, 'config.yaml')
    with open(config_path, 'w') as f:
        f.write(
            "MAX_HEADING_LENGTH: 7\n"
            "MAX_SENTENCE_LENGTH: 400\n"
            "MAX_PARAGRAPH_LENGTH: 1000\n"
            "MAX_FALLBACK_LENGTH: 800\n"
            "MAX_CODE_BLOCK_LENGTH: 1500\n"
            "MAX_TABLE_LENGTH: 2000\n"
            "MAX_QUOTED_TEXT_LENGTH: 300\n"
            "MAX_LIST_ITEM_LENGTH: 200\n"
            "MAX_LIST_ITEM_COUNT: 6\n"
            "MAX_LIST_INDENT_SPACES: 7\n"
            "MAX_BLOCKQUOTE_CONTENT_LENGTH: 200\n"
            "MAX_BLOCKQUOTE_LINES: 15\n"
            "MAX_CODE_LANGUAGE_LENGTH: 20\n"
            "MAX_INDENTED_CODE_LINES: 20\n"
            "MAX_TABLE_ROW_LENGTH: 200\n"
            "MAX_TABLE_ROW_COUNT: 20\n"
            "MIN_HORIZONTAL_RULE_LENGTH: 3\n"
            "MAX_HR_LENGTH: 3\n"
            "MAX_PARENTHETICAL_CONTENT_LENGTH: 200\n"
            "MAX_NESTED_PARENTHESES: 5\n"
            "MAX_MATH_INLINE_LENGTH: 100\n"
            "MAX_MATH_BLOCK_LENGTH: 500\n"
            "MAX_STANDALONE_LINE_LENGTH: 800\n"
            "MAX_HTML_TAG_ATTRIBUTES_LENGTH: 100\n"
            "MAX_HTML_TAG_CONTENT_LENGTH: 1000\n"
            "MAX_HTML_STYLE_LENGTH: 100\n"
            "MAX_HTML_STYLE_CONTENT_LENGTH: 1000\n"
            "MAX_LATEX_LENGTH: 500\n"
            "MAX_CITATIONS_LENGTH: 800\n"
            "MAX_HEADING_CONTENT_LENGTH: 200\n"
            "MAX_HEADING_UNDERLINE_LENGTH: 200\n"
            "MAX_HTML_HEADING_ATTRIBUTES_LENGTH: 100\n"
            "OVERLAP_CHARS: 50\n"
            "MIN_TOKEN_THRESHOLD: 5\n"
            "LOOKAHEAD_RANGE: 100\n"
        )
    return config_path


@pytest.fixture
def sample_patterns(tmp_dir):
    patterns_path = os.path.join(tmp_dir, 'patterns.json')
    patterns = {
        "headings": r"^#{1,7}\s+\S.+",
        "sentence": r"[^\r\n]{1,400}[.!?](?=\s|$)",
        "fallback": r"[^\r\n]{1,800}",
    }
    with open(patterns_path, 'w') as f:
        json.dump(patterns, f)
    return patterns_path


@pytest.fixture
def chunker(sample_config, sample_patterns):
    return TextChunker(
        config_file=sample_config,
        regex_file=sample_patterns,
    )


# ── Coverage Analyzer ────────────────────────────────────────────────

class TestCoverageAnalyzer:
    def test_full_coverage(self, chunker):
        """简单文本应该有高覆盖率"""
        text = "# Hello World\nThis is a test sentence."
        chunks = chunker.chunk_text(text)
        analyzer = CoverageAnalyzer(chunker)
        report = analyzer.analyze(text, chunks)
        assert report['coverage_ratio'] >= 0.5
        assert report['total_chars'] == len(text)

    def test_empty_text(self, chunker):
        """空文本覆盖率应为 0"""
        analyzer = CoverageAnalyzer(chunker)
        report = analyzer.analyze("")
        assert report['coverage_ratio'] == 0.0
        assert report['total_chars'] == 0

    def test_no_chunks(self, chunker):
        """无 chunk 时覆盖率应为 0"""
        analyzer = CoverageAnalyzer(chunker)
        report = analyzer.analyze("Hello world", chunks=[])
        assert report['coverage_ratio'] == 0.0

    def test_gap_detection(self, chunker):
        """gap 检测应返回未覆盖区域"""
        text = "# Title\nSome text here. More text."
        chunks = chunker.chunk_text(text)
        analyzer = CoverageAnalyzer(chunker)
        report = analyzer.analyze(text, chunks)
        assert 'gaps' in report
        assert isinstance(report['gaps'], list)

    def test_coverage_ratio_range(self, chunker):
        """覆盖率应在 0-1 之间"""
        text = "# Hello\nThis is a test. And another one."
        chunks = chunker.chunk_text(text)
        analyzer = CoverageAnalyzer(chunker)
        report = analyzer.analyze(text, chunks)
        assert 0.0 <= report['coverage_ratio'] <= 1.0


# ── Overlap Sliding Window ──────────────────────────────────────────

class TestOverlapSlidingWindow:
    def test_no_overlap(self):
        """overlap_chars=0 不添加重叠"""
        chunks = [
            {'text': 'Hello world.', 'type': 'sentence', 'token_count': 2},
            {'text': 'Goodbye world.', 'type': 'sentence', 'token_count': 2},
        ]
        window = OverlapSlidingWindow(overlap_chars=0)
        result = window.apply(chunks)
        assert len(result) == 2
        assert all('overlap_prefix' not in c for c in result)

    def test_with_overlap(self):
        """overlap_chars>0 应添加重叠字段"""
        chunks = [
            {'text': 'Hello world. This is a test.', 'type': 'sentence', 'token_count': 6},
            {'text': 'Goodbye world. See you later.', 'type': 'sentence', 'token_count': 6},
        ]
        window = OverlapSlidingWindow(overlap_chars=10)
        result = window.apply(chunks)
        assert len(result) == 2
        # 第一个 chunk 应有 overlap_suffix
        assert 'overlap_suffix' in result[0]
        assert len(result[0]['overlap_suffix']) <= 10
        # 第二个 chunk 应有 overlap_prefix
        assert 'overlap_prefix' in result[1]
        assert len(result[1]['overlap_prefix']) <= 10

    def test_single_chunk(self):
        """单个 chunk 不应有重叠"""
        chunks = [
            {'text': 'Hello world.', 'type': 'sentence', 'token_count': 2},
        ]
        window = OverlapSlidingWindow(overlap_chars=50)
        result = window.apply(chunks)
        assert len(result) == 1
        assert result[0].get('overlap_prefix', '') == ''
        assert result[0].get('overlap_suffix', '') == ''

    def test_empty_chunks(self):
        """空 chunks 列表应返回空"""
        window = OverlapSlidingWindow(overlap_chars=50)
        result = window.apply([])
        assert result == []

    def test_remove_overlap(self):
        """去除重叠应还原原始文本"""
        window = OverlapSlidingWindow(overlap_chars=10)
        text = "prefix_text_real_content_suffix_text"
        prefix = "prefix_text_"
        suffix = "_suffix_text"
        result = window.remove_overlap(prefix + "real_content" + suffix, prefix, suffix)
        assert result == "real_content"


# ── Streaming Iterator ────────────────────────────────────────────────

class TestStreamingChunker:
    def test_chunk_text_iter(self, sample_config, sample_patterns):
        """流式分块应返回与批量相同的结果"""
        text = "# Hello World\nThis is a test sentence. And another one."
        chunker = TextChunker(config_file=sample_config, regex_file=sample_patterns)
        batch_result = chunker.chunk_text(text)

        streamer = StreamingChunker(config=sample_config, patterns=sample_patterns)
        stream_result = list(streamer.chunk_text_iter(text))

        # 流式结果应与批量结果数量一致
        assert len(stream_result) == len(batch_result)
        for s, b in zip(stream_result, batch_result):
            assert s['text'] == b['text']
            assert s['type'] == b['type']

    def test_chunk_file_iter(self, sample_config, sample_patterns, tmp_dir):
        """流式文件分块应正常工作"""
        input_file = os.path.join(tmp_dir, 'stream_test.txt')
        with open(input_file, 'w') as f:
            f.write("# Title\nHello world. Goodbye world.")

        streamer = StreamingChunker(config=sample_config, patterns=sample_patterns)
        result = list(streamer.chunk_file_iter(input_file))
        assert len(result) >= 1

    def test_chunk_file_iter_not_found(self, sample_config, sample_patterns):
        """不存在的文件应抛出异常"""
        streamer = StreamingChunker(config=sample_config, patterns=sample_patterns)
        with pytest.raises(TokenizerError):
            list(streamer.chunk_file_iter("/nonexistent/file.txt"))

    def test_stats_updated(self, sample_config, sample_patterns):
        """流式分块后统计应更新"""
        text = "# Hello\nThis is a test. And another."
        streamer = StreamingChunker(config=sample_config, patterns=sample_patterns)
        list(streamer.chunk_text_iter(text))
        assert streamer.stats['total_chunks'] > 0


# ── Smart Chunk Merge ────────────────────────────────────────────────

class TestSmartChunkMerger:
    def test_merge_adjacent_same_type(self):
        """相邻同类型块应合并"""
        chunks = [
            {'text': 'Hello world.', 'type': 'sentence', 'token_count': 2},
            {'text': ' Goodbye world.', 'type': 'sentence', 'token_count': 2},
        ]
        merger = SmartChunkMerger(max_merge_length=1500)
        result = merger.merge(chunks)
        assert len(result) == 1
        assert 'Hello world.' in result[0]['text']
        assert 'Goodbye world.' in result[0]['text']

    def test_no_merge_different_type(self):
        """不同类型块不应合并（token 数高于阈值时）"""
        chunks = [
            {'text': 'Hello world. This is a longer sentence.', 'type': 'sentence', 'token_count': 8},
            {'text': '# Title Heading Here', 'type': 'headings', 'token_count': 6},
        ]
        merger = SmartChunkMerger(max_merge_length=1500, min_token_threshold=5)
        result = merger.merge(chunks)
        assert len(result) == 2

    def test_merge_small_chunks(self):
        """低 token 数碎片应合并到前一块"""
        chunks = [
            {'text': 'Hello world.', 'type': 'sentence', 'token_count': 10},
            {'text': '#tag', 'type': 'hashtag', 'token_count': 1},
        ]
        merger = SmartChunkMerger(max_merge_length=1500, min_token_threshold=5)
        result = merger.merge(chunks)
        assert len(result) == 1

    def test_empty_chunks(self):
        """空列表应返回空"""
        merger = SmartChunkMerger()
        result = merger.merge([])
        assert result == []

    def test_single_chunk(self):
        """单个块应原样返回"""
        chunks = [{'text': 'Hello world.', 'type': 'sentence', 'token_count': 2}]
        merger = SmartChunkMerger()
        result = merger.merge(chunks)
        assert len(result) == 1

    def test_split_oversized(self):
        """超大块应被拆分（含段落边界）"""
        long_text = "A" * 300 + "\n\n" + "B" * 300 + "\n\n" + "C" * 300
        chunks = [{'text': long_text, 'type': 'fallback', 'token_count': 900}]
        merger = SmartChunkMerger(max_merge_length=500)
        result = merger.merge(chunks)
        assert len(result) > 1


# ── NDJSON Stream ────────────────────────────────────────────────────

class TestNDJSONWriter:
    def test_write_to_stdout(self, capsys):
        """写入 stdout 应输出 NDJSON"""
        writer = NDJSONWriter(buffer_size=1)
        writer.write({'text': 'hello', 'type': 'sentence'})
        writer.close()
        captured = capsys.readouterr()
        assert 'hello' in captured.out
        assert '\n' in captured.out

    def test_write_to_file(self, tmp_dir):
        """写入文件应正确保存"""
        output_file = os.path.join(tmp_dir, 'test.ndjson')
        writer = NDJSONWriter(output_file=output_file, buffer_size=1)
        writer.write({'text': 'hello', 'type': 'sentence'})
        writer.write({'text': 'world', 'type': 'sentence'})
        writer.close()

        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) == 2
        for line in lines:
            record = json.loads(line.strip())
            assert 'text' in record

    def test_buffer_flush(self, tmp_dir):
        """缓冲区满时应自动刷新"""
        output_file = os.path.join(tmp_dir, 'buffer_test.ndjson')
        writer = NDJSONWriter(output_file=output_file, buffer_size=3)
        for i in range(5):
            writer.write({'text': f'chunk_{i}', 'type': 'sentence'})
        writer.close()

        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) == 5


class TestNDJSONReader:
    def test_read_file(self, tmp_dir):
        """从文件读取 NDJSON 应正确解析"""
        input_file = os.path.join(tmp_dir, 'input.ndjson')
        with open(input_file, 'w') as f:
            f.write('{"text": "hello", "type": "sentence"}\n')
            f.write('{"text": "world", "type": "sentence"}\n')

        reader = NDJSONReader(input_file=input_file)
        records = list(reader.read_file())
        assert len(records) == 2
        assert records[0]['text'] == 'hello'

    def test_skip_malformed(self, tmp_dir):
        """畸形 JSON 行应被跳过（不返回）"""
        input_file = os.path.join(tmp_dir, 'malformed.ndjson')
        with open(input_file, 'w') as f:
            f.write('{"text": "hello"}\n')
            f.write('not json\n')
            f.write('{"text": "world"}\n')

        reader = NDJSONReader(input_file=input_file)
        records = list(reader.read_file())
        # 畸形行被跳过，只返回有效记录
        assert len(records) == 2
        assert records[0]['text'] == 'hello'
        assert records[1]['text'] == 'world'


# ── v3.2 API Integration ────────────────────────────────────────────

class TestV32API:
    def test_chunk_text_with_smart_merge(self, sample_config, sample_patterns):
        """API 应支持 smart_merge 参数"""
        from tokenizer.api import chunk_text
        result = chunk_text(
            "# Hello\nThis is a test. And another.",
            config=sample_config, patterns=sample_patterns,
            smart_merge=True
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_chunk_text_with_overlap(self, sample_config, sample_patterns):
        """API 应支持 overlap_chars 参数"""
        from tokenizer.api import chunk_text
        result = chunk_text(
            "# Hello\nThis is a test. And another.",
            config=sample_config, patterns=sample_patterns,
            overlap_chars=50
        )
        assert isinstance(result, list)
        assert all('overlap_prefix' in c or 'overlap_suffix' in c for c in result)

    def test_chunk_text_with_coverage(self, sample_config, sample_patterns):
        """API 应支持 coverage 参数"""
        from tokenizer.api import chunk_text
        result = chunk_text(
            "# Hello\nThis is a test. And another.",
            config=sample_config, patterns=sample_patterns,
            coverage=True
        )
        assert isinstance(result, dict)
        assert 'chunks' in result
        assert 'coverage' in result
        assert 'coverage_ratio' in result['coverage']
