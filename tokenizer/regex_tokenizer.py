#
# # Updated: Aug. 15, 2024
# Run: python testRegex.py testText.txt
# Used in https://jina.ai/tokenizer

"""
This script is used to test the performance of the chunking algorithm.
It reads a text file and chunks it into sentences or phrases.
It also prints the total number of characters, words, and sentences.
# @author: Hertz
# @time: 2024/8/20
# @version: 2.1
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
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree.ElementTree import Element, SubElement, ElementTree


class TextChunker:
    def __init__(self, config_file='config.yaml', regex_file='patterns.json', output_file='output.jsonl', stats_file='stats.json'):
        self.output_file = output_file
        self.stats_file = stats_file
        self.config = self.load_config(config_file)
        self.regex_patterns = self.load_and_substitute_regex_patterns(regex_file, self.config)
        self.compile_chunk_regex()
        self.setup_logging()
        self.stats = {
            'total_tokens': 0,
            'total_chunks': 0,
            'total_characters': 0,
            'total_lines': 0,
            'chunk_details': []
        }

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML config file: {e}")
            sys.exit(1)

    def load_and_substitute_regex_patterns(self, regex_file, config):
        try:
            with open(regex_file, 'r') as file:
                patterns = json.load(file)
        except FileNotFoundError:
            logging.error(f"Regex file not found: {regex_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON regex file: {e}")
            sys.exit(1)

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

    def format_bytes(self, size):
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def measure_performance(self, text):
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

    def save_results(self, matches, output_format='jsonl'):
        if output_format == 'jsonl':
            self.save_results_to_jsonl(matches)
        elif output_format == 'csv':
            self.save_results_to_csv(matches)
        elif output_format == 'xml':
            self.save_results_to_xml(matches)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_results_to_jsonl(self, matches):
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for match in matches:
                    json.dump(match, f, ensure_ascii=False)
                    f.write('\n')
            logging.info(f"Results saved to {self.output_file}")
        except IOError as e:
            logging.error(f"Error writing to file {self.output_file}: {e}")

    def save_results_to_csv(self, matches):
        csv_file = self.output_file.replace('.jsonl', '.csv')
        try:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['text', 'type', 'token_count'])
                writer.writeheader()
                for match in matches:
                    writer.writerow(match)
            logging.info(f"Results saved to {csv_file}")
        except IOError as e:
            logging.error(f"Error writing to file {csv_file}: {e}")

    def save_results_to_xml(self, matches):
        root = Element('chunks')
        for match in matches:
            chunk_elem = SubElement(root, 'chunk')
            text_elem = SubElement(chunk_elem, 'text')
            text_elem.text = match['text']
            type_elem = SubElement(chunk_elem, 'type')
            type_elem.text = match['type']
            token_elem = SubElement(chunk_elem, 'token_count')
            token_elem.text = str(match['token_count'])
        tree = ElementTree(root)
        xml_file = self.output_file.replace('.jsonl', '.xml')
        try:
            tree.write(xml_file, encoding='utf-8')
            logging.info(f"Results saved to {xml_file}")
        except IOError as e:
            logging.error(f"Error writing to file {xml_file}: {e}")

    def save_patterns_to_json(self, file_path='patterns.json'):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.patterns_dict, file, ensure_ascii=False, indent=2)
            logging.info(f"Patterns saved to {file_path}")
        except IOError as e:
            logging.error(f"Error writing to file {file_path}: {e}")

    def save_stats(self):
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            logging.info(f"Statistics saved to {self.stats_file}")
        except IOError as e:
            logging.error(f"Error writing to file {self.stats_file}: {e}")

    def process_text(self, text):
        try:
            matches, execution_time, memory_used = self.measure_performance(text)
            self.print_results(matches, execution_time, memory_used)
            self.save_results(matches)
            self.save_stats()
        except Exception as e:
            logging.error(f"Error processing text: {e}")

    def process_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            self.process_text(text)
        except IOError as e:
            logging.error(f"Error reading file {file_path}: {e}")

    def process_large_file(self, file_path, chunk_size=1024*1024):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output file', nargs='?',
                        default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
    parser.add_argument('--regex', type=str, help='Path to the JSON regex config file', default='patterns.json')
    parser.add_argument('--chunk_size', type=int, help='Chunk size for processing large files', default=1024*1024)
    parser.add_argument('--output_format', type=str, help='Output format (jsonl, csv, xml)', default='jsonl')
    parser.add_argument('--num_threads', type=int, help='Number of threads for parallel processing', default=4)
    parser.add_argument('--stats_file', type=str, help='Path to the output statistics file', default='stats.json')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        logging.error(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(config_file=args.config, regex_file=args.regex, output_file=args.output_file, stats_file=args.stats_file)

    try:
        if os.path.getsize(args.file_path) > args.chunk_size:
            chunker.process_large_file(args.file_path, chunk_size=args.chunk_size)
        else:
            chunker.process_file(args.file_path)

        with open(args.file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        matches = chunker.process_text_in_parallel(text, num_threads=args.num_threads)
        chunker.print_results(matches, 0, 0)  # Execution time and memory usage are not calculated here for simplicity
        chunker.save_results(matches, output_format=args.output_format)
        chunker.save_stats()
    except Exception as e:
        logging.error(f"Error in main execution: {e}")