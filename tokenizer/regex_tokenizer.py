# Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

"""
This script is used to test the performance of the chunking algorithm.
It reads a text file and chunks it into sentences or phrases.
It also prints the total number of characters, words, and sentences.
@author: Hertz
@time: 2024/8/20
@version: 1.0
"""
import json
import re
import sys
import time
import os
import psutil
import argparse

class TextChunker:
    def __init__(self, output_file='output.json'):
        self.output_file = output_file
        self.define_patterns()
        self.compile_chunk_regex()

    def define_patterns(self):
        # Define variables for magic numbers
        self.MAX_HEADING_LENGTH = 7
        self.MAX_HEADING_CONTENT_LENGTH = 200
        self.MAX_HEADING_UNDERLINE_LENGTH = 200
        self.MAX_HTML_HEADING_ATTRIBUTES_LENGTH = 100
        self.MAX_LIST_ITEM_LENGTH = 200
        self.MAX_NESTED_LIST_ITEMS = 6
        self.MAX_LIST_INDENT_SPACES = 7
        self.MAX_BLOCKQUOTE_LINE_LENGTH = 200
        self.MAX_BLOCKQUOTE_LINES = 15
        self.MAX_CODE_BLOCK_LENGTH = 1500
        self.MAX_CODE_LANGUAGE_LENGTH = 20
        self.MAX_INDENTED_CODE_LINES = 20
        self.MAX_TABLE_CELL_LENGTH = 200
        self.MAX_TABLE_ROWS = 20
        self.MAX_HTML_TABLE_LENGTH = 2000
        self.MIN_HORIZONTAL_RULE_LENGTH = 3
        self.MAX_SENTENCE_LENGTH = 400  # Adjusted to match code 2
        self.MAX_QUOTED_TEXT_LENGTH = 300
        self.MAX_PARENTHETICAL_CONTENT_LENGTH = 200
        self.MAX_NESTED_PARENTHESES = 5
        self.MAX_MATH_INLINE_LENGTH = 100
        self.MAX_MATH_BLOCK_LENGTH = 500
        self.MAX_PARAGRAPH_LENGTH = 1000
        self.MAX_STANDALONE_LINE_LENGTH = 800
        self.MAX_HTML_TAG_ATTRIBUTES_LENGTH = 100
        self.MAX_HTML_TAG_CONTENT_LENGTH = 1000
        self.LOOKAHEAD_RANGE = 100  # Adjusted to match code 2

    def compile_chunk_regex(self):
        # Define regex patterns
        headings_pattern = (
            f"(?:^(?:[#*=-]{{1,{self.MAX_HEADING_LENGTH}}}|\\w[^\\r\\n]{{0,{self.MAX_HEADING_CONTENT_LENGTH}}}\\r?\\n[-=]{{2,{self.MAX_HEADING_UNDERLINE_LENGTH}}}|<h[1-6][^>]{{0,{self.MAX_HTML_HEADING_ATTRIBUTES_LENGTH}}}>)[^\\r\\n]{{1,{self.MAX_HEADING_CONTENT_LENGTH}}}(?:</h[1-6]>)?(?:\\r?\\n|$))"
        )

        # New pattern for citations
        citations_pattern = f"(?:\$[0-9]+\$[^\\r\\n]{{1,{self.MAX_STANDALONE_LINE_LENGTH}}})"

        list_item_base = (
            f"(?:[-*+•]|\\d{{1,3}}\\.\\w\\.|\$[ xX]\$)[ \\t]+"
            f"(?:(?:\\b[^\\r\\n]{{1,{self.MAX_LIST_ITEM_LENGTH}}}\\b"
            f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])(?=\\s|$))"
            f"|(?:\\b[^\\r\\n]{{1,{self.MAX_LIST_ITEM_LENGTH}}}\\b(?=[\\r\\n]|$))"
            f"|(?:\\b[^\\r\\n]{{1,{self.MAX_LIST_ITEM_LENGTH}}}\\b"
            f"(?=[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])"
            f"(?:.{{1,{self.LOOKAHEAD_RANGE}}}"
            f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])(?=\\s|$))?))"
        )

        nested_list_item = (
            f"(?:\\r?\\n[ \\t]{{2,5}}{list_item_base})"
            f"{{0,{self.MAX_NESTED_LIST_ITEMS}}}"
        )

        deep_nested_list_item = (
            f"(?:\\r?\\n[ \\t]{{4,{self.MAX_LIST_INDENT_SPACES}}}{list_item_base})"
            f"{{0,{self.MAX_NESTED_LIST_ITEMS}}}"
        )

        list_items_pattern = (
            f"(?:(?:^|\\r?\\n)[ \\t]{{0,3}}{list_item_base}"
            f"{nested_list_item}"
            f"{deep_nested_list_item})"
        )

        blockquote_line_base = (
            f"(?:(?:\\b[^\\r\\n]{{0,{self.MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b"
            f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])(?=\\s|$))"
            f"|(?:\\b[^\\r\\n]{{0,{self.MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b(?=[\\r\\n]|$))"
            f"|(?:\\b[^\\r\\n]{{0,{self.MAX_BLOCKQUOTE_LINE_LENGTH}}}\\b"
            f"(?=[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])"
            f"(?:.{{1,{self.LOOKAHEAD_RANGE}}}"
            f"(?:[.!?…]|\\.{3}|[\\u2026\\u2047-\\u2049]|[\\U0001F600-\\U0001F64F])(?=\\s|$))?))"
        )

        block_quote = (
            f"(?:(?:^>\\s?(?:>|\\s{{2,}}){{0,2}}{blockquote_line_base}\\r?\\n?)"
            f"{{1,{self.MAX_BLOCKQUOTE_LINES}}})"
        )

        code_block = (
            f"(?:(?:^|\\r?\\n)(?:```|~~~)(?:\\w{{0,{self.MAX_CODE_LANGUAGE_LENGTH}}})?\\r?\\n[\\s\\S]{{0,{self.MAX_CODE_BLOCK_LENGTH}}}?(?:```|~~~)\\r?\\n?"
            f"|(?:(?:^|\\r?\\n)(?: {{4}}|\\t)[^\\r\\n]{{0,{self.MAX_LIST_ITEM_LENGTH}}}(?:\\r?\\n(?: {{4}}|\\t)[^\\r\\n]{{0,{self.MAX_LIST_ITEM_LENGTH}}}){{0,{self.MAX_INDENTED_CODE_LINES}}}\\r?\\n?)"
            f"|(?:<pre>(?:<code>)?[\\s\\S]{{0,{self.MAX_CODE_BLOCK_LENGTH}}}?(?:</code>)?</pre>))"
        )

        table_pattern = (
            f"(?:(?:^|\r?\n)(?:\\|[^\\r\\n]{{0,{self.MAX_TABLE_CELL_LENGTH}}}\\|(?:\\r?\\n\\|[-:]{{1,{self.MAX_TABLE_CELL_LENGTH}}}\\|){{0,1}}(?:\\r?\\n\\|[^\\r\\n]{{0,{self.MAX_TABLE_CELL_LENGTH}}}\\|){{0,{self.MAX_TABLE_ROWS}}})"
            f"|<table>[\s\S]{{0,{self.MAX_HTML_TABLE_LENGTH}}}?</table>)"
        )

        horizontal_rule_pattern = (
            f"(?:^(?:[-*_]){{1,{self.MIN_HORIZONTAL_RULE_LENGTH}}}\\s*$|<hr\\s*/?>)"
        )

        sentence_pattern = (
            f"(?:(?:[^\r\n]{{1,{self.MAX_SENTENCE_LENGTH}}}(?:[.!?…]|\.{{3}}|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))"
            f"|(?:[^\r\n]{{1,{self.MAX_SENTENCE_LENGTH}}}(?=[\r\n]|$))"
            f"|(?:[^\r\n]{{1,{self.MAX_SENTENCE_LENGTH}}}(?=[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])"
            f"(?:.{{1,{self.LOOKAHEAD_RANGE}}}(?:[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))?))"
        )

        quoted_text = (
                rf"(?:" +
                rf"(?<!\w)\"\"\"[^\"]{{0,{self.MAX_QUOTED_TEXT_LENGTH}}}\"\"\"(?!\w)" +
                rf"|(?<!\w)(?:\"[^\r\n]{{0,{self.MAX_QUOTED_TEXT_LENGTH}}}\"|\'[^\r\n]{{0,{self.MAX_QUOTED_TEXT_LENGTH}}}\'|\`[^\r\n]{{0,{self.MAX_QUOTED_TEXT_LENGTH}}}\`)(?!\w)" +
                rf"|\([^\r\n()]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:\([^\r\n()]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}\)[^\r\n()]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{self.MAX_NESTED_PARENTHESES}}}\)" +
                rf"|$[^\r\n$$]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}(?:$[^\r\n$$]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}$[^\r\n$$]{{0,{self.MAX_PARENTHETICAL_CONTENT_LENGTH}}}){{0,{self.MAX_NESTED_PARENTHESES}}}$" +
                rf"|\$[^\r\n$]{{0,{self.MAX_MATH_INLINE_LENGTH}}}\$" +
                rf"|\`[^\`\r\n]{{0,{self.MAX_MATH_INLINE_LENGTH}}}\`" +
                rf")"
        )

        paragraph_pattern = (
            rf"(?:(?:^|\r?\n\r?\n)(?:<p>)?(?:(?:[^\r\n]{{1,{self.MAX_PARAGRAPH_LENGTH}}}(?:[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))|(?:[^\r\n]{{1,{self.MAX_PARAGRAPH_LENGTH}}}(?=[\r\n]|$))|(?:[^\r\n]{{1,{self.MAX_PARAGRAPH_LENGTH}}}(?=[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?:.{{1,{self.LOOKAHEAD_RANGE}}}(?:[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))?))(?:</p>)?(?=\r?\n\r?\n|$))"
        )

        html_style_pattern = (
            rf"(?:<[a-zA-Z][^>]{{0,{self.MAX_HTML_TAG_ATTRIBUTES_LENGTH}}}(?:>[\s\S]{{0,{self.MAX_HTML_TAG_CONTENT_LENGTH}}}?</[a-zA-Z]+>|\s*/>))"
        )

        latex_style_pattern = (
            rf"(?:(?:\$\$[\s\S]{{0,{self.MAX_MATH_BLOCK_LENGTH}}}?\$\$)|(?:\$[^\$\r\n]{{0,{self.MAX_MATH_INLINE_LENGTH}}}\$))"
        )

        fallback_pattern = (
            rf"(?:(?:[^\r\n]{{1,{self.MAX_STANDALONE_LINE_LENGTH}}}(?:[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))|(?:[^\r\n]{{1,{self.MAX_STANDALONE_LINE_LENGTH}}}(?=[\r\n]|$))|(?:[^\r\n]{{1,{self.MAX_STANDALONE_LINE_LENGTH}}}(?=[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?:.{{1,{self.LOOKAHEAD_RANGE}}}(?:[.!?…]|\.\.\.|[\u2026\u2047-\u2049]|[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF])(?=\s|$))?))"
        )

        chunk_patterns = [
            headings_pattern,
            citations_pattern,
            list_items_pattern,
            block_quote,
            code_block,
            table_pattern,
            horizontal_rule_pattern,
            sentence_pattern,
            quoted_text,
            paragraph_pattern,
            html_style_pattern,
            latex_style_pattern,
            fallback_pattern
        ]

        self.chunk_regex = re.compile(
            "|".join(chunk_patterns),
            re.MULTILINE | re.UNICODE
        )

    def chunk_text(self, text):
        """Chunk the input text using the regex pattern."""
        return self.chunk_regex.findall(text)

    def format_bytes(self, size):
        """Convert bytes to a human-readable string."""
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0


    def measure_performance(self, text):
        """Measure the performance of the regex chunking."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss

        matches = self.chunk_text(text)

        end_time = time.time()
        end_memory = process.memory_info().rss

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        return matches, execution_time, memory_used


    def print_results(self, matches, execution_time, memory_used):
        """Print the results of the regex chunking."""
        print(f"Number of chunks: {len(matches) if matches else 0}")
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Memory used: {self.format_bytes(memory_used)}")

        print('\nFirst 10 chunks:')
        if matches:
            for match in matches[:10]:
                print(repr(match)[:50])
        else:
            print('No chunks found.')

        print(f"\nRegex flags: {self.chunk_regex.flags}")

        if execution_time > 5:
            print('\nWarning: Execution time exceeded 5 seconds. The regex might be too complex or the input too large.')
        if memory_used > 100 * 1024 * 1024:
            print('\nWarning: Memory usage exceeded 100 MB. Consider processing the input in smaller chunks.')



    def print_results(self, matches, execution_time, memory_used):
        """Print the results of the regex chunking."""
        print(f"Number of chunks: {len(matches) if matches else 0}")
        print(f"Execution time: {execution_time:.3f} seconds")
        print(f"Memory used: {self.format_bytes(memory_used)}")

        print('\nFirst 10 chunks:')
        if matches:
            for match in matches[:10]:
                print(repr(match)[:50])
        else:
            print('No chunks found.')

        print(f"\nRegex flags: {self.chunk_regex.flags}")

        if execution_time > 5:
            print(
                '\nWarning: Execution time exceeded 5 seconds. The regex might be too complex or the input too large.')
        if memory_used > 100 * 1024 * 1024:
            print('\nWarning: Memory usage exceeded 100 MB. Consider processing the input in smaller chunks.')

    def save_results_to_json(self, matches):
        """Save the results of the regex chunking to a JSON file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=4)
        print(f"Results saved to {self.output_file}")

    def process_text(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        matches, execution_time, memory_used = self.measure_performance(text)
        self.print_results(matches, execution_time, memory_used)
        self.save_results_to_json(matches)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output JSON file', nargs='?', default='output.json')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(args.output_file)
    chunker.process_text(args.file_path)