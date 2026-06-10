"""Regex Tokenizer 入口脚本

修复：合并双路径为单次处理路径，避免统计翻倍
"""

import argparse
import os
import sys
import logging

from tokenizer.processor import TextProcessor
from tokenizer.regex_tokenizer import TextChunker
from tokenizer.exceptions import TokenizerError


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

    try:
        chunker = TextChunker(config_file=args.config, regex_file=args.regex)
        processor = TextProcessor(
            chunker, output_file=args.output_file,
            stats_file=args.stats_file, num_threads=args.num_threads
        )

        # 统一为单次处理路径（修复双重处理 Bug）
        if os.path.getsize(args.file_path) > args.chunk_size:
            processor.process_large_file(args.file_path, chunk_size=args.chunk_size)
        else:
            processor.process_file(args.file_path)

    except TokenizerError as e:
        logging.error(f"Tokenizer error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
