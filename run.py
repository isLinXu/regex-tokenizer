# import logging
# import os
# import sys
# import argparse
#
# from tokenizer.loader import load_config, load_and_substitute_regex_patterns
# from tokenizer.logger_setup import setup_logging
# from tokenizer.regex_tokenizer import TextChunker
# from tokenizer.result_saver import save_results, save_stats

# def main():
#     parser = argparse.ArgumentParser(description='Chunk text file.')
#     parser.add_argument('file_path', type=str, help='Path to the text file')
#     parser.add_argument('output_file', type=str, help='Path to the output file', nargs='?', default='output.jsonl')
#     parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
#     parser.add_argument('--regex', type=str, help='Path to the JSON regex config file', default='patterns.json')
#     parser.add_argument('--chunk_size', type=int, help='Chunk size for processing large files', default=1024 * 1024)
#     parser.add_argument('--output_format', type=str, help='Output format (jsonl, csv, xml, excel)',default='jsonl')
#     parser.add_argument('--num_threads', type=int, help='Number of threads for parallel processing', default=4)
#     parser.add_argument('--stats_file', type=str, help='Path to the output statistics file', default='stats.json')
#     args = parser.parse_args()
#
#     if not os.path.exists(args.file_path):
#         logging.error(f"File not found: {args.file_path}")
#         sys.exit(1)
#
#     setup_logging()
#
#     config = load_config(args.config)
#     regex_patterns = load_and_substitute_regex_patterns(args.regex, config)
#     chunker = TextChunker(config, regex_patterns)
#
#     try:
#         if os.path.getsize(args.file_path) > args.chunk_size:
#             chunker.process_large_file(args.file_path, chunk_size=args.chunk_size)
#         else:
#             chunker.process_file(args.file_path)
#
#         with open(args.file_path, 'r', encoding='utf-8') as file:
#             text = file.read()
#         matches, execution_time, memory_used = chunker.process_text_in_parallel_with_performance(text, num_threads=args.num_threads)
#         chunker.print_results(matches, execution_time, memory_used)
#         save_results(matches, args.output_file, output_format=args.output_format)
#         save_stats(chunker.stats, args.stats_file)
#     except Exception as e:
#         logging.error(f"Error in main execution: {e}")
#
# if __name__ == "__main__":
#     main()

import argparse
import os
import sys
import logging

from tokenizer.processor import TextProcessor
from tokenizer.regex_tokenizer import TextChunker

def main():
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output file', nargs='?', default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
    parser.add_argument('--regex', type=str, help='Path to the JSON regex config file', default='patterns.json')
    parser.add_argument('--chunk_size', type=int, help='Chunk size for processing large files', default=1024 * 1024)
    parser.add_argument('--output_format', type=str, help='Output format (jsonl, csv, xml, excel)', default='jsonl')
    parser.add_argument('--num_threads', type=int, help='Number of threads for parallel processing', default=1)
    parser.add_argument('--stats_file', type=str, help='Path to the output statistics file', default='stats.json')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        logging.error(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(config_file=args.config, regex_file=args.regex)
    processor = TextProcessor(chunker, output_file=args.output_file, stats_file=args.stats_file)

    try:
        if os.path.getsize(args.file_path) > args.chunk_size:
            processor.process_large_file(args.file_path, chunk_size=args.chunk_size)
        else:
            processor.process_file(args.file_path)

        with open(args.file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        matches, execution_time, memory_used = processor.process_text_in_parallel_with_performance(text, num_threads=args.num_threads)
        processor.print_results(matches, execution_time, memory_used)
        processor.save_results(matches, output_format=args.output_format)
        processor.save_stats()
    except Exception as e:
        logging.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()