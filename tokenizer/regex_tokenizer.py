#
# # Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

"""
This script is used to test the performance of the chunking algorithm.
It reads a text file and chunks it into sentences or phrases.
It also prints the total number of characters, words, and sentences.
# @author: Hertz
# @time: 2024/8/26
# @version: 2.4
"""
import re
import logging
from .loader import load_config
from .loader import load_and_substitute_regex_patterns
from .logger_setup import setup_logging

class TextChunker:
    def __init__(self, config_file='config.yaml', regex_file='patterns.json'):
        self.config = load_config(config_file)
        self.regex_patterns = load_and_substitute_regex_patterns(regex_file, self.config)
        self.compile_chunk_regex()
        setup_logging()
        self.stats = {
            'total_tokens': 0,
            'total_chunks': 0,
            'total_characters': 0,
            'total_lines': 0,
            'chunk_details': []
        }

    def compile_chunk_regex(self):
        self.patterns_dict = self.regex_patterns
        chunk_patterns = list(self.regex_patterns.values())
        self.chunk_regex = re.compile(
            "|".join(chunk_patterns),
            re.MULTILINE | re.UNICODE
        )

    def chunk_text(self, text):
        matches = self.chunk_regex.finditer(text)
        chunks = []
        for match in matches:
            chunk_text = match.group().strip()
            if chunk_text:  # Check if the chunk is not empty
                for name, pattern in self.patterns_dict.items():
                    if re.fullmatch(pattern, chunk_text):
                        token_count = len(chunk_text.split())
                        self.stats['total_tokens'] += token_count
                        self.stats['total_chunks'] += 1
                        self.stats['total_characters'] += len(chunk_text)
                        self.stats['total_lines'] += chunk_text.count('\n') + 1
                        self.stats['chunk_details'].append({
                            'text': chunk_text,
                            'type': name,
                            'token_count': token_count,
                            'character_count': len(chunk_text),
                            'line_count': chunk_text.count('\n') + 1
                        })
                        chunks.append({'text': chunk_text, 'type': name, 'token_count': token_count})
                        break
        return chunks

    def update_regex_patterns(self, new_patterns):
        """
        Dynamically update regex patterns.
        :param new_patterns: Dictionary of new regex patterns.
        """
        self.regex_patterns.update(new_patterns)
        self.compile_chunk_regex()
