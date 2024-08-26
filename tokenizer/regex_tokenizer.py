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
# @version: 2.2
"""
import re
import logging
import os
import psutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .result_saver import save_results, save_stats
from .performance_measurer import measure_performance, format_bytes

class TextChunker:
    def __init__(self, config, regex_patterns):
        self.stats_file = None
        self.output_file = None
        self.config = config
        self.regex_patterns = regex_patterns
        self.compile_chunk_regex()
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

    def process_text(self, text):
        try:
            matches, execution_time, memory_used = measure_performance(self.chunk_text, text)
            self.print_results(matches, execution_time, memory_used)
            save_results(matches, self.output_file)
            save_stats(self.stats, self.stats_file)
        except Exception as e:
            logging.error(f"Error processing text: {e}")

    def process_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            self.process_text(text)
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")

    def process_large_file(self, file_path, chunk_size=1024 * 1024):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = []
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    text.append(chunk)
                    if len(text) > 0:
                        self.process_text(''.join(text))
                        text = []
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")

    def process_text_in_parallel(self, text, num_threads=4):
        chunk_size = len(text) // num_threads
        futures = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i in range(num_threads):
                start = i * chunk_size
                end = None if i == num_threads - 1 else (i + 1) * chunk_size
                futures.append(executor.submit(self.chunk_text, text[start:end]))

            all_matches = []
            for future in as_completed(futures):
                try:
                    all_matches.extend(future.result())
                except Exception as e:
                    logging.error(f"Error in thread execution: {e}")

        return all_matches

    def process_text_in_parallel_with_performance(self, text, num_threads=4):
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss

        matches = self.process_text_in_parallel(text, num_threads)

        end_time = time.time()
        end_memory = process.memory_info().rss

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        return matches, execution_time, memory_used

    def print_results(self, matches, execution_time, memory_used):
        logging.info(f"Number of chunks: {len(matches) if matches else 0}")
        logging.info(f"Execution time: {execution_time:.3f} seconds")
        logging.info(f"Memory used: {format_bytes(memory_used)}")

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


