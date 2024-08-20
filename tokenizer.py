# Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

import re
import regex as re
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
# MAX_SENTENCE_LENGTH = 400
MAX_SENTENCE_LENGTH = 1000
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
# 定义列表项的基本模式
list_item_base = (
    f"(?:[-*+•]|\\d{{1,3}}\\.\\w\\.|\\[[ xX]\\])[ \\t]+"
    f"(?:(?:\\b[^\\r\\n]{{1,{MAX_LIST_ITEM_LENGTH}}}\\b"
    f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])(?=\\s|$))"
    f"|(?:\\b[^\\r\\n]{{1,{MAX_LIST_ITEM_LENGTH}}}\\b(?=[\\r\\n]|$))"
    f"|(?:\\b[^\\r\\n]{{1,{MAX_LIST_ITEM_LENGTH}}}\\b"
    f"(?=[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])"
    f"(?:.{{1,{LOOKAHEAD_RANGE}}}"
    f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])(?=\\s|$))?))"
)

# 定义嵌套列表项的模式
nested_list_item = (
    f"(?:\\r?\\n[ \\t]{{2,5}}{list_item_base})"
    f"{{0,{MAX_NESTED_LIST_ITEMS}}}"
)

# 定义更深层嵌套列表项的模式
deep_nested_list_item = (
    f"(?:\\r?\\n[ \\t]{{4,{MAX_LIST_INDENT_SPACES}}}{list_item_base})"
    f"{{0,{MAX_NESTED_LIST_ITEMS}}}"
)

# 组合所有部分
list_items_pattern = (
    f"(?:(?:^|\\r?\\n)[ \\t]{{0,3}}{list_item_base}"
    f"{nested_list_item}"
    f"{deep_nested_list_item})"
)


# 3. Block quotes (including nested quotes and citations, up to three levels, with length constraints)
# 定义块引用行的基本模式
blockquote_line_base = (
    f"(?:(?:\\b[^\\r\\n]{{0,{MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b"
    f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])(?=\\s|$))"
    f"|(?:\\b[^\\r\\n]{{0,{MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b(?=[\\r\\n]|$))"
    f"|(?:\\b[^\\r\\n]{{0,{MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b"
    f"(?=[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])"
    f"(?:.{{1,{LOOKAHEAD_RANGE}}}"
    f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\p{{Emoji_Presentation}}\\p{{Extended_Pictographic}}])(?=\\s|$))?))"
)

# 定义块引用的模式
block_quote = (
    f"(?:(?:^>\\s?(?:>|\\s{{2,}}){{0,2}}{blockquote_line_base}\\r?\\n?)"
    f"{{1,{MAX_BLOCKQUOTE_LINES}}})"
)


# 4. Code blocks (fenced, indented, or HTML pre/code tags, with length constraints)
code_block=(
    f"(?:(?:^|\\r?\\n)(?:```|~~~)(?:\\w{{0,{MAX_CODE_LANGUAGE_LENGTH}}})?\\r?\\n[\\s\\S]{{0,{MAX_CODE_BLOCK_LENGTH}}}?(?:```|~~~)\\r?\\n?"
    f"|(?:(?:^|\\r?\\n)(?: {{4}}|\\t)[^\\r\\n]{{0,{MAX_LIST_ITEM_LENGTH}}}(?:\\r?\\n(?: {{4}}|\\t)[^\\r\\n]{{0,{MAX_LIST_ITEM_LENGTH}}}){{0,{MAX_INDENTED_CODE_LINES}}}\\r?\\n?)"
    f"|(?:<pre>(?:<code>)?[\\s\\S]{{0,{MAX_CODE_BLOCK_LENGTH}}}?(?:</code>)?</pre>))"
)

# 5. Tables (Markdown, grid tables, and HTML tables, with length constraints)
table_pattern = (
    f"(?:(?:^|\r?\n)(?:\\|[^\\r\\n]{{0,{MAX_TABLE_CELL_LENGTH}}}\\|(?:\\r?\\n\\|[-:]{{1,{MAX_TABLE_CELL_LENGTH}}}\\|){{0,1}}(?:\\r?\\n\\|[^\\r\\n]{{0,{MAX_TABLE_CELL_LENGTH}}}\\|){{0,{MAX_TABLE_ROWS}}})"
    f"|<table>[\s\S]{{0,{MAX_HTML_TABLE_LENGTH}}}?</table>)"
)

# 6. Horizontal rules (Markdown and HTML hr tag)
horizontal_rule_pattern = (
    f"(?:^(?:[-*_]){{1,{MIN_HORIZONTAL_RULE_LENGTH}}}\\s*$|<hr\\s*/?>)"
)

# 7. Sentences or phrases ending with punctuation (including ellipsis and Unicode punctuation)
sentence_pattern = (
    f"(?:(?:[^\r\n]{{1,{MAX_SENTENCE_LENGTH}}}(?:[.!?…]|\.{{3}}|[\u2026\u2047-\u2049]|[\p{{Emoji_Presentation}}\p{{Extended_Pictographic}}])(?=\s|$))|(?:[^\r\n]{{1,{MAX_SENTENCE_LENGTH}}}(?=[\r\n]|$))|(?:[^\r\n]{{1,{MAX_SENTENCE_LENGTH}}}(?=[.!?…]|\.{{3}}|[\u2026\u2047-\u2049]|[\p{{Emoji_Presentation}}\p{{Extended_Pictographic}}])(?:.{{1,{LOOKAHEAD_RANGE}}}(?:[.!?…]|\.{{3}}|[\u2026\u2047-\u2049]|[\p{{Emoji_Presentation}}\p{{Extended_Pictographic}}])(?=\s|$))?))"
)

# 8. Quoted text, parenthetical phrases, or bracketed content (with length constraints)
quoted_text = (
    rf"(?:" +
    rf"(?<!\w)\"\"\"[^\"]{{0,{MAX_QUOTED_TEXT_LENGTH}}}\"\"\"(?!\w)" +
    rf"|(?<!\w)(?:\"[^\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}\"|\'[^\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}\'|\`[^\r\n]{{0,{MAX_QUOTED_TEXT_LENGTH}}}\`)(?!\w)" +
    rf"|\([^\r\n()]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:\([^\r\n()]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}\)[^\r\n()]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{MAX_NESTED_PARENTHESES}}}\)" +
    rf"|\[[^\r\n\[\]]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:\[[^\r\n\[\]]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}\][^\r\n\[\]]{{0,{MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{MAX_NESTED_PARENTHESES}}}\]" +
    rf"|\$[^\r\n$]{{0,{MAX_MATH_INLINE_LENGTH}}}\$" +
    rf"|\`[^\`\r\n]{{0,{MAX_MATH_INLINE_LENGTH}}}\`" +
    rf")"
)

# 9. Paragraphs (with length constraints)
paragraph_pattern = (
    rf"(?:(?:^|\r?\n\r?\n)(?:<p>)?(?:(?:[^\r\n]{{1,{MAX_PARAGRAPH_LENGTH}}}(?:[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))|(?:[^\r\n]{{1,{MAX_PARAGRAPH_LENGTH}}}(?=[\r\n]|$))|(?:[^\r\n]{{1,{MAX_PARAGRAPH_LENGTH}}}(?=[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?:.{{1,{LOOKAHEAD_RANGE}}}(?:[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))?))(?:</p>)?(?=\r?\n\r?\n|$))"
)

# 11. HTML-like tags and their content (including self-closing tags and attributes, with length constraints)
html_style_pattern = (
    rf"(?:<[a-zA-Z][^>]{{0,{MAX_HTML_TAG_ATTRIBUTES_LENGTH}}}(?:>[\s\S]{{0,{MAX_HTML_TAG_CONTENT_LENGTH}}}?</[a-zA-Z]+>|\s*/>))"
)

# 12. LaTeX-style math expressions (inline and block, with length constraints)
latex_style_pattern = (
    rf"(?:(?:\$\$[\s\S]{{0,{MAX_MATH_BLOCK_LENGTH}}}?\$\$)|(?:\$[^\$\r\n]{{0,{MAX_MATH_INLINE_LENGTH}}}\$))"
)

# # 14. Fallback for any remaining content (with length constraints)
fallback_pattern = (
    rf"(?:(?:[^\r\n]{{1,{MAX_STANDALONE_LINE_LENGTH}}}(?:[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))|(?:[^\r\n]{{1,{MAX_STANDALONE_LINE_LENGTH}}}(?=[\r\n]|$))|(?:[^\r\n]{{1,{MAX_STANDALONE_LINE_LENGTH}}}(?=[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?:.{{1,{LOOKAHEAD_RANGE}}}(?:[.!?…]|\.{{3}}|\u2026|\u2047-\u2049|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))?))"
)

chunk_regex = re.compile(
    "("
    + headings_pattern
    + "|"
    + citations_pattern
    + "|"
    + list_items_pattern
    + "|"
    + block_quote
    + "|"
    + code_block
    + "|"
    + table_pattern
    + "|"
    + horizontal_rule_pattern
    + "|"
    + sentence_pattern
    + "|"
    + quoted_text
    + "|"
    + paragraph_pattern
    + "|"
    + html_style_pattern
    + "|"
    + latex_style_pattern
    + "|"
    + fallback_pattern
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


