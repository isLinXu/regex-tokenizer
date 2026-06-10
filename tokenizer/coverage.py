"""Coverage Analysis & Gap Detection - v3.2

解决 RAG 场景漏匹配不可见问题。
核心思路：对比原文与所有 chunk 拼接后的文本，找出未被任何模式匹配到的"间隙"。

用法:
    from tokenizer.coverage import CoverageAnalyzer

    analyzer = CoverageAnalyzer(chunker)
    report = analyzer.analyze(text)
    # report = {
    #   'coverage_ratio': 0.95,
    #   'total_chars': 1000,
    #   'covered_chars': 950,
    #   'gap_count': 3,
    #   'gaps': [{'start': 10, 'end': 20, 'text': '...'}, ...]
    # }
"""

from typing import Dict, List, Any


class CoverageAnalyzer:
    """覆盖率分析器 - 检测正则匹配遗漏的文本区域"""

    def __init__(self, chunker=None):
        self._chunker = chunker

    def analyze(self, text: str, chunks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析文本覆盖率，检测 gap。

        Args:
            text: 原始输入文本
            chunks: 已分块结果（若为 None 则自动调用 chunker）

        Returns:
            dict: 覆盖率报告
        """
        if chunks is None and self._chunker is not None:
            chunks = self._chunker.chunk_text(text)

        if not chunks:
            return {
                'coverage_ratio': 0.0,
                'total_chars': len(text),
                'covered_chars': 0,
                'gap_count': len(text),
                'gaps': self._find_all_gaps(text, []),
            }

        # 构建已覆盖的字符位置集合
        covered = self._build_covered_set(text, chunks)
        covered_chars = len(covered)
        total_chars = len(text)
        coverage_ratio = covered_chars / total_chars if total_chars > 0 else 0.0

        # 找出 gap
        gaps = self._find_all_gaps(text, chunks)

        return {
            'coverage_ratio': round(coverage_ratio, 4),
            'total_chars': total_chars,
            'covered_chars': covered_chars,
            'gap_count': len(gaps),
            'gaps': gaps,
        }

    def _build_covered_set(self, text: str, chunks: List[Dict[str, Any]]) -> set:
        """构建已覆盖字符位置的集合。

        通过在原文中查找每个 chunk 文本的位置来标记覆盖。
        """
        covered = set()
        remaining = text
        offset = 0

        for chunk in chunks:
            chunk_text = chunk.get('text', '')
            if not chunk_text:
                continue
            # 在剩余文本中查找 chunk 的位置
            idx = remaining.find(chunk_text)
            if idx != -1:
                for i in range(idx, idx + len(chunk_text)):
                    covered.add(offset + i)
                # 移动偏移
                remaining = remaining[idx + len(chunk_text):]
                offset += idx + len(chunk_text)
            else:
                # chunk 文本不在原文中（可能被修改），尝试全局搜索
                idx = text.find(chunk_text)
                if idx != -1:
                    for i in range(idx, idx + len(chunk_text)):
                        covered.add(i)

        return covered

    def _find_all_gaps(self, text: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """找出所有未被覆盖的连续文本区域（gap）。"""
        covered = self._build_covered_set(text, chunks) if chunks else set()
        gaps = []
        gap_start = None

        for i in range(len(text)):
            if i not in covered:
                if gap_start is None:
                    gap_start = i
            else:
                if gap_start is not None:
                    gap_text = text[gap_start:i]
                    # 过滤掉纯空白 gap
                    if gap_text.strip():
                        gaps.append({
                            'start': gap_start,
                            'end': i - 1,
                            'length': i - gap_start,
                            'text': gap_text[:200],  # 截断预览
                        })
                    gap_start = None

        # 处理末尾 gap
        if gap_start is not None:
            gap_text = text[gap_start:]
            if gap_text.strip():
                gaps.append({
                    'start': gap_start,
                    'end': len(text) - 1,
                    'length': len(text) - gap_start,
                    'text': gap_text[:200],
                })

        return gaps
