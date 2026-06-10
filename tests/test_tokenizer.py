"""Regex Tokenizer v3.0 单元测试

覆盖：token 计数、分块逻辑、异常处理、配置加载、语义分割。
"""

import os
import json
import tempfile
import pytest

# 让项目根目录可导入
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tokenizer.regex_tokenizer import TextChunker, count_tokens
from tokenizer.processor import TextProcessor, _safe_split_text
from tokenizer.loader import load_config, load_and_substitute_regex_patterns
from tokenizer.exceptions import (
    TokenizerError, ConfigError, PatternError, ExportError, TimeoutError,
)


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


# ── count_tokens ──────────────────────────────────────────────────────

class TestCountTokens:
    def test_whitespace(self):
        assert count_tokens("hello world foo", method='whitespace') == 3

    def test_character(self):
        assert count_tokens("hello world", method='character') == 10  # 不含空格

    def test_auto_cjk(self):
        # 中文为主 -> 按字符计数
        text = "这是一个中文句子用来测试"
        assert count_tokens(text, method='auto') == sum(
            1 for c in text if not c.isspace()
        )

    def test_auto_latin(self):
        # 英文为主 -> 按 whitespace 计数
        assert count_tokens("hello world foo", method='auto') == 3

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="Unknown token count method"):
            count_tokens("test", method='invalid')


# ── TextChunker ──────────────────────────────────────────────────────

class TestTextChunker:
    def test_basic_chunking(self, chunker):
        text = "# Hello World\nThis is a sentence. And another one."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert all('text' in c and 'type' in c and 'token_count' in c for c in chunks)

    def test_heading_recognized(self, chunker):
        text = "# Main Title"
        chunks = chunker.chunk_text(text)
        assert any(c['type'] == 'headings' for c in chunks)

    def test_sentence_recognized(self, chunker):
        text = "This is a sentence. And another one."
        chunks = chunker.chunk_text(text)
        assert any(c['type'] == 'sentence' for c in chunks)

    def test_stats_updated(self, chunker):
        text = "# Title\nHello world. Goodbye world."
        chunker.chunk_text(text)
        assert chunker.stats['total_chunks'] > 0
        assert chunker.stats['total_tokens'] > 0
        assert isinstance(chunker.stats['type_distribution'], dict)

    def test_empty_input(self, chunker):
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_cjk_text(self, chunker):
        text = "这是一个测试句子。另一句话。"
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1


# ── Loader ────────────────────────────────────────────────────────────

class TestLoader:
    def test_load_config_missing(self):
        with pytest.raises(ConfigError, match="Config file not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_valid(self, sample_config):
        config = load_config(sample_config)
        assert isinstance(config, dict)
        assert 'MAX_HEADING_LENGTH' in config

    def test_load_patterns_missing(self):
        with pytest.raises(PatternError, match="Regex file not found"):
            load_and_substitute_regex_patterns(
                "/nonexistent/path/patterns.json", {}
            )

    def test_placeholder_substitution(self, sample_config, sample_patterns):
        config = load_config(sample_config)
        patterns = load_and_substitute_regex_patterns(sample_patterns, config)
        # 确保 {MAX_...} 占位符已被替换
        for val in patterns.values():
            assert '{MAX_' not in val


# ── Exceptions ────────────────────────────────────────────────────────

class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(ConfigError, TokenizerError)
        assert issubclass(PatternError, TokenizerError)
        assert issubclass(ExportError, TokenizerError)
        assert issubclass(TimeoutError, TokenizerError)

    def test_raise_catch(self):
        with pytest.raises(TokenizerError):
            raise ConfigError("test")


# ── _safe_split_text ──────────────────────────────────────────────────

class TestSafeSplitText:
    def test_short_text_unchanged(self):
        text = "Hello world"
        result = _safe_split_text(text, 1000)
        assert len(result) == 1
        assert result[0] == text

    def test_splits_at_paragraph_boundary(self):
        text = "A" * 500 + "\n\n" + "B" * 500
        result = _safe_split_text(text, 600)
        assert len(result) >= 2

    def test_preserves_content(self):
        text = "Hello world"
        result = _safe_split_text(text, 5)
        assert "".join(result) == text


# ── TextProcessor ────────────────────────────────────────────────────

class TestTextProcessor:
    def test_process_small_file(self, chunker, tmp_dir):
        input_file = os.path.join(tmp_dir, 'input.txt')
        output_file = os.path.join(tmp_dir, 'output.jsonl')
        stats_file = os.path.join(tmp_dir, 'stats.json')

        with open(input_file, 'w') as f:
            f.write("# Title\nHello world. Goodbye.")

        processor = TextProcessor(chunker, output_file=output_file,
                                  stats_file=stats_file)
        processor.process_file(input_file)

        assert os.path.exists(output_file)
        assert os.path.exists(stats_file)

    def test_process_large_file(self, chunker, tmp_dir):
        input_file = os.path.join(tmp_dir, 'large_input.txt')
        output_file = os.path.join(tmp_dir, 'output.jsonl')
        stats_file = os.path.join(tmp_dir, 'stats.json')

        # 生成超过 chunk_size 的文本
        with open(input_file, 'w') as f:
            f.write("# Title\n" + "Hello world. " * 5000)

        processor = TextProcessor(chunker, output_file=output_file,
                                  stats_file=stats_file)
        processor.process_large_file(input_file, chunk_size=1024)

        assert os.path.exists(output_file)


# ── Integration ───────────────────────────────────────────────────────

class TestIntegration:
    def test_full_pipeline(self, sample_config, sample_patterns, tmp_dir):
        input_file = os.path.join(tmp_dir, 'test.txt')
        output_file = os.path.join(tmp_dir, 'test.jsonl')
        stats_file = os.path.join(tmp_dir, 'test_stats.json')

        with open(input_file, 'w') as f:
            f.write("# Document Title\n\nFirst sentence here. Second sentence there.\n")

        chunker = TextChunker(config_file=sample_config, regex_file=sample_patterns)
        processor = TextProcessor(chunker, output_file=output_file,
                                  stats_file=stats_file)
        processor.process_file(input_file)

        # 验证输出
        assert os.path.exists(output_file)
        with open(output_file) as f:
            lines = f.readlines()
            assert len(lines) >= 1
            for line in lines:
                record = json.loads(line)
                assert 'text' in record
                assert 'type' in record

        # 验证统计
        assert os.path.exists(stats_file)
        with open(stats_file) as f:
            stats = json.load(f)
            assert stats['total_chunks'] >= 1
