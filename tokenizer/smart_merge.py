"""Smart Chunk Merge - v3.2

解决 hashtag/mention 碎片块问题。
将相邻的同类型小块合并为更大的语义完整块。

策略：
1. 类型一致性：相邻同类型块合并
2. 大小阈值：token 数低于阈值的块优先合并
3. 大块拆分：超过最大长度的块按语义边界拆分

用法:
    from tokenizer.smart_merge import SmartChunkMerger

    merger = SmartChunkMerger(max_merge_length=1500, min_token_threshold=5)
    merged = merger.merge(chunks)
"""

import logging
from typing import List, Dict, Any

from .regex_tokenizer import count_tokens


class SmartChunkMerger:
    """智能块合并器 - 合并相邻同类型碎片块"""

    def __init__(self, max_merge_length=1500, min_token_threshold=5):
        self.max_merge_length = max_merge_length
        self.min_token_threshold = min_token_threshold

    def merge(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并相邻块。

        Args:
            chunks: 待合并的块列表

        Returns:
            合并后的块列表
        """
        if not chunks:
            return []

        # Phase 1: 合并相邻同类型小块
        merged = self._merge_adjacent_same_type(chunks)

        # Phase 2: 合并低 token 数碎片
        merged = self._merge_small_chunks(merged)

        # Phase 3: 拆分超大块
        result = self._split_oversized(merged)

        return result

    def _merge_adjacent_same_type(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并相邻同类型块"""
        if not chunks:
            return []

        merged = [dict(chunks[0])]
        for i in range(1, len(chunks)):
            prev = merged[-1]
            curr = chunks[i]

            prev_text = prev.get('text', '')
            curr_text = curr.get('text', '')

            # 同类型 + 合并后不超过最大长度
            if (prev.get('type') == curr.get('type') and
                    prev_text and curr_text and
                    len(prev_text) + len(curr_text) <= self.max_merge_length):
                prev['text'] = prev_text + curr_text
                prev['token_count'] = prev.get('token_count', 0) + curr.get('token_count', 0)
            else:
                merged.append(dict(curr))

        return merged

    def _merge_small_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并低 token 数碎片块（如 hashtag/mention）"""
        if not chunks:
            return []

        merged = [dict(chunks[0])]
        for i in range(1, len(chunks)):
            prev = merged[-1]
            curr = chunks[i]

            curr_tokens = curr.get('token_count', 0)
            prev_text = prev.get('text', '')
            curr_text = curr.get('text', '')

            # 当前块 token 数低于阈值 → 合并到前一块
            if (curr_tokens < self.min_token_threshold and
                    prev_text and curr_text and
                    len(prev_text) + len(curr_text) <= self.max_merge_length):
                prev['text'] = prev_text + ' ' + curr_text
                prev['token_count'] = prev.get('token_count', 0) + curr_tokens
            else:
                merged.append(dict(curr))

        return merged

    def _split_oversized(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """拆分超过最大长度的块"""
        result = []
        for chunk in chunks:
            text = chunk.get('text', '')
            if len(text) <= self.max_merge_length:
                result.append(chunk)
                continue

            # 按段落边界拆分
            sub_chunks = self._split_by_paragraph(chunk)
            result.extend(sub_chunks)

        return result

    def _split_by_paragraph(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按段落边界拆分超大块"""
        text = chunk.get('text', '')
        chunk_type = chunk.get('type', 'fallback')

        # 按双换行拆分
        paragraphs = text.split('\n\n')
        result = []
        current_text = ''
        current_tokens = 0

        for para in paragraphs:
            para_text = para.strip()
            if not para_text:
                continue

            if len(current_text) + len(para_text) + 2 <= self.max_merge_length:
                if current_text:
                    current_text += '\n\n' + para_text
                else:
                    current_text = para_text
                current_tokens = count_tokens(current_text, method='auto')
            else:
                if current_text:
                    result.append({
                        'text': current_text,
                        'type': chunk_type,
                        'token_count': current_tokens,
                    })
                current_text = para_text
                current_tokens = count_tokens(para_text, method='auto')

        if current_text:
            result.append({
                'text': current_text,
                'type': chunk_type,
                'token_count': current_tokens,
            })

        return result if result else [chunk]
