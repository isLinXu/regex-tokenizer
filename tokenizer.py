# Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

import re
# import regex as re
import sys
import time
import os
import psutil

# Define variables for magic numbers
MAX_HEADING_LENGTH = 7
MAX_HEADING_CONTENT_LENGTH = 200
MAX_HEADING_UNDERLINE_LENGTH = 200
MAX_HTML_HEADING_ATTRIBUTES_LENGTH = 100
MAX_LIST_ITEM_LENGTH = 200
MAX_NESTED_LIST_ITEMS = 6
MAX_LIST_INDENT_SPACES = 7
MAX_BLOCKQUOTE_LINE_LENGTH = 200
MAX_BLOCKQUOTE_LINES = 15
MAX_CODE_BLOCK_LENGTH = 1500
MAX_CODE_LANGUAGE_LENGTH = 20
MAX_INDENTED_CODE_LINES = 20
MAX_TABLE_CELL_LENGTH = 200
MAX_TABLE_ROWS = 20
MAX_HTML_TABLE_LENGTH = 2000
MIN_HORIZONTAL_RULE_LENGTH = 3
MAX_SENTENCE_LENGTH = 400
MAX_QUOTED_TEXT_LENGTH = 300
MAX_PARENTHETICAL_CONTENT_LENGTH = 200
MAX_NESTED_PARENTHESES = 5
MAX_MATH_INLINE_LENGTH = 100
MAX_MATH_BLOCK_LENGTH = 500
MAX_PARAGRAPH_LENGTH = 1000
MAX_STANDALONE_LINE_LENGTH = 800
MAX_HTML_TAG_ATTRIBUTES_LENGTH = 100
MAX_HTML_TAG_CONTENT_LENGTH = 1000
LOOKAHEAD_RANGE = 100  # Number of characters to look ahead for a sentence boundary

# 1. Headings (Setext-style, Markdown, and HTML-style, with length constraints)
headings_pattern = (
    f"(?:^(?:[#*=-]{{1,{MAX_HEADING_LENGTH}}}|\\w[^\\r\\n]{{0,{MAX_HEADING_CONTENT_LENGTH}}}\\r?\\n[-=]{{2,{MAX_HEADING_UNDERLINE_LENGTH}}}|<h[1-6][^>]{{0,{MAX_HTML_HEADING_ATTRIBUTES_LENGTH}}}>)[^\\r\\n]{{1,{MAX_HEADING_CONTENT_LENGTH}}}(?:</h[1-6]>)?(?:\\r?\\n|$))"
)

# New pattern for citations
citations_pattern = f"(?:\\[[0-9]+\\][^\\r\\n]+)"

# 2. List items (bulleted, numbered, lettered, or task lists, including nested, up to three levels, with length constraints)
list_items_pattern = (r"(?:(?:^|\r?\n)[ \t]{0,3}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?))"
          r"(?:(?:\r?\n[ \t]{2,5}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?)))"
          r"{0," + str(MAX_NESTED_LIST_ITEMS) + r"}(?:\r?\n[ \t]{4," + str(MAX_LIST_INDENT_SPACES) + r"}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?)))"
          r"{0," + str(MAX_NESTED_LIST_ITEMS) + r"}?)")


pattern = (r"(?:(?:^|\r?\n)[ \t]{0,3}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?))"
          r"(?:(?:\r?\n[ \t]{2,5}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?)))"
          r"{0," + str(MAX_NESTED_LIST_ITEMS) + r"}(?:\r?\n[ \t]{4," + str(MAX_LIST_INDENT_SPACES) + r"}(?:[-*+•]|\d{1,3}\.\w\.|\[[ xX]\])[ \t]+(?:(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[\r\n]|$))|(?:\b[^\r\n]{1," + str(MAX_LIST_ITEM_LENGTH) + r"}\b(?=[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?:.{1," + str(LOOKAHEAD_RANGE) + r"}(?:[.!?…]|\.{3}|[\u2026\u2047-\u2049]|[\p{Emoji_Presentation}\p{Extended_Pictographic}])(?=\s|$))?)))"
          r"{0," + str(MAX_NESTED_LIST_ITEMS) + r"}?)")
chunk_regex = re.compile(
    "("
    + headings_pattern
    + "|"
    + citations_pattern
    + "|"
    # pattern
    + ")",
    re.MULTILINE | re.UNICODE
)

# Read from the arg[1] file
with open(sys.argv[1], 'r', encoding='utf-8') as file:
    test_text = file.read()

# Function to format bytes to a human-readable string
# 定义一个函数，将字节数格式化为可读字符串
def format_bytes(bytes):
    if bytes < 1024:
        return f"{bytes} bytes"
    elif bytes < 1048576:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1073741824:
        return f"{bytes / 1048576:.2f} MB"
    else:
        return f"{bytes / 1073741824:.2f} GB"

# 开始测量时间和内存
start_time = time.time()
process = psutil.Process(os.getpid())
start_memory = process.memory_info().rss

# 应用正则表达式
matches = re.findall(chunk_regex, test_text)

# 结束测量时间和内存
end_time = time.time()
end_memory = process.memory_info().rss

# 计算执行时间和内存使用
execution_time = end_time - start_time
memory_used = end_memory - start_memory

# 输出结果
print(f"Number of chunks: {len(matches) if matches else 0}")
print(f"Execution time: {execution_time:.3f} seconds")
print(f"Memory used: {format_bytes(memory_used)}")

# 输出前10个匹配项（如果少于10个则输出所有）
print('\nFirst 10 chunks:')
if matches:
    for match in matches[:10]:
        print(repr(match)[:50])
else:
    print('No chunks found.')

# 输出正则表达式的标志
print(f"\nRegex flags: {chunk_regex.flags}")

# 检查潜在问题
if execution_time > 5:
    print('\nWarning: Execution time exceeded 5 seconds. The regex might be too complex or the input too large.')
if memory_used > 100 * 1024 * 1024:
    print('\nWarning: Memory usage exceeded 100 MB. Consider processing the input in smaller chunks.')


