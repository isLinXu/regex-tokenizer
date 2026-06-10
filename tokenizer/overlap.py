"""Overlap Sliding Window - v3.2

解决相邻 chunk 上下文断裂问题。
通过在相邻块之间添加重叠区域，确保跨块语义连续性。

用法:
    from tokenizer.overlap import OverlapSlidingWindow

    window = OverlapSlidingWindow(overlap_chars=50)
    overlapped = window.apply(chunks)
    # 每个 chunk 的 text 末尾会包含下一 chunk 开头的 overlap 部分
"""

from typing import List, Dict, Any


class OverlapSlidingWindow:
    """重叠滑动窗口 - 为相邻 chunk 添加上下文重叠。

    策略：
    1. 从下一 chunk 开头取 overlap_chars 个字符追加到当前 chunk
    2. 从上一 chunk 末尾取 overlap_chars 个字符前置到当前 chunk
    3. 重叠部分标记为 metadata.overlap=true，便于下游去重
    """

    def __init__(self, overlap_chars=50):
        self.overlap_chars = overlap_chars

    def apply(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为 chunk 列表添加重叠上下文。

        Args:
            chunks: 原始分块结果

        Returns:
            添加重叠后的分块结果
        """
        if not chunks or self.overlap_chars <= 0:
            return chunks

        result = []
        for i, chunk in enumerate(chunks):
            new_chunk = dict(chunk)  # 浅拷贝
            text = chunk.get('text', '')

            # 前向重叠：从上一 chunk 末尾取
            prefix = ''
            if i > 0:
                prev_text = chunks[i - 1].get('text', '')
                prefix = prev_text[-self.overlap_chars:] if len(prev_text) >= self.overlap_chars else prev_text

            # 后向重叠：从下一 chunk 开头取
            suffix = ''
            if i < len(chunks) - 1:
                next_text = chunks[i + 1].get('text', '')
                suffix = next_text[:self.overlap_chars] if len(next_text) >= self.overlap_chars else next_text

            new_chunk['text'] = text
            new_chunk['overlap_prefix'] = prefix
            new_chunk['overlap_suffix'] = suffix
            new_chunk['overlap_chars'] = len(prefix) + len(suffix)

            result.append(new_chunk)

        return result

    def remove_overlap(self, text: str, overlap_prefix: str = '', overlap_suffix: str = '') -> str:
        """去除重叠部分，还原原始 chunk 文本。

        Args:
            text: chunk 文本
            overlap_prefix: 前向重叠文本
            overlap_suffix: 后向重叠文本

        Returns:
            去除重叠后的文本
        """
        result = text
        if overlap_prefix and result.startswith(overlap_prefix):
            result = result[len(overlap_prefix):]
        if overlap_suffix and result.endswith(overlap_suffix):
            result = result[:-len(overlap_suffix)]
        return result
