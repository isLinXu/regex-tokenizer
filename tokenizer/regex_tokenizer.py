
# Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

"""
This script is used to test the performance of the chunking algorithm.
It reads a text file and chunks it into sentences or phrases.
It also prints the total number of characters, words, and sentences.
# @author: Hertz
# @time: 2024/8/20
# @version: 1.2
"""

import json
import logging
import re
import sys
import time
import os
import psutil
import argparse
import yaml


class TextChunker:
    def __init__(self, config_file='config.yaml', regex_file='patterns.json', output_file='output.jsonl'):
        self.output_file = output_file
        self.config = self.load_config(config_file)
        self.regex_patterns = self.load_and_substitute_regex_patterns(regex_file, self.config)
        self.compile_chunk_regex()
        self.setup_logging()

    def load_config(self, config_file):
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)

    def load_and_substitute_regex_patterns(self, regex_file, config):
        with open(regex_file, 'r') as file:
            patterns = json.load(file)

        # Substitute placeholders with config values
        for key, pattern in patterns.items():
            for config_key, config_value in config.items():
                placeholder = f"{{{config_key}}}"
                pattern = pattern.replace(placeholder, str(config_value))
            patterns[key] = pattern

        return patterns

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def compile_chunk_regex(self):
        # Load regex patterns from JSON configuration
        self.patterns_dict = self.regex_patterns

        chunk_patterns = list(self.regex_patterns.values())

        self.chunk_regex = re.compile(
            "|".join(chunk_patterns),
            re.MULTILINE | re.UNICODE
        )

    def chunk_text(self, text):
        """Chunk the input text using the regex pattern."""
        matches = self.chunk_regex.finditer(text)
        chunks = []
        for match in matches:
            chunk_text = match.group().strip()
            if chunk_text:  # Check if the chunk is not empty
                for name, pattern in self.patterns_dict.items():
                    if re.fullmatch(pattern, chunk_text):
                        chunks.append({'text': chunk_text, 'type': name})
                        break
        return chunks

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
        logging.info(f"Number of chunks: {len(matches) if matches else 0}")
        logging.info(f"Execution time: {execution_time:.3f} seconds")
        logging.info(f"Memory used: {self.format_bytes(memory_used)}")

        logging.info('\nFirst 10 chunks:')
        if matches:
            for match in matches[:10]:
                logging.info(repr(match)[:50])
        else:
            logging.info('No chunks found.')

        logging.info(f"\nRegex flags: {self.chunk_regex.flags}")

        if execution_time > 5:
            logging.warning('Execution time exceeded 5 seconds. The regex might be too complex or the input too large.')
        if memory_used > 100 * 1024 * 1024:
            logging.warning('Memory usage exceeded 100 MB. Consider processing the input in smaller chunks.')

    def save_results_to_jsonl(self, matches):
        """Save the results of the regex chunking to a JSONL file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for match in matches:
                json.dump(match, f, ensure_ascii=False)
                f.write('\n')
        print(f"Results saved to {self.output_file}")

    def save_patterns_to_json(self, file_path='patterns.json'):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(self.patterns_dict, file, ensure_ascii=False, indent=2)
        print(f"Patterns saved to {file_path}")

    def process_text(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        matches, execution_time, memory_used = self.measure_performance(text)
        self.print_results(matches, execution_time, memory_used)
        self.save_results_to_jsonl(matches)
        self.save_patterns_to_json()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output JSONL file', nargs='?',
                            default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
    parser.add_argument('--regex', type=str, help='Path to the JSON regex config file', default='regex_config.json')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(config_file=args.config, regex_file=args.regex, output_file=args.output_file)
    chunker.process_text(args.file_path)