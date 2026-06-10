"""Regex Tokenizer 入口脚本

修复：合并双路径为单次处理路径，避免统计翻倍
v3.1: 集成性能测量、输出摘要、embedding 格式
"""

import argparse
import os
import sys
import logging

from tokenizer.processor import TextProcessor
from tokenizer.regex_tokenizer import TextChunker
from tokenizer.performance_measurer import measure_performance, format_bytes
from tokenizer.exceptions import TokenizerError, ExportError


def main():
    parser = argparse.ArgumentParser(
        description='Regex Tokenizer - 高性能文本分块器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py input.txt output.jsonl
  python run.py input.md out.jsonl --regex patterns_new.json --num_threads 4
  python run.py input.md out.jsonl --output_format embedding
  python run.py input.md out.jsonl --token_method character
        """
    )
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output file',
                        nargs='?', default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file',
                        default='config.yaml')
    parser.add_argument('--regex', type=str, help='Path to the JSON regex config file',
                        default='patterns.json')
    parser.add_argument('--chunk_size', type=int,
                        help='Chunk size for processing large files',
                        default=1024 * 1024)
    parser.add_argument('--output_format', type=str,
                        help='Output format (jsonl, csv, xml, excel, embedding)',
                        default='jsonl')
    parser.add_argument('--num_threads', type=int,
                        help='Number of threads for parallel processing', default=1)
    parser.add_argument('--stats_file', type=str,
                        help='Path to the output statistics file', default='stats.json')
    parser.add_argument('--token_method', type=str,
                        help='Token count method (auto, whitespace, character)',
                        default='auto')
    parser.add_argument('--timeout', type=float,
                        help='Regex matching timeout in seconds', default=5.0)
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        logging.error(f"File not found: {args.file_path}")
        sys.exit(1)

    try:
        chunker = TextChunker(
            config_file=args.config, regex_file=args.regex,
            token_method=args.token_method, regex_timeout=args.timeout
        )
        processor = TextProcessor(
            chunker, output_file=args.output_file,
            stats_file=args.stats_file, num_threads=args.num_threads
        )

        # 带性能测量的处理
        if os.path.getsize(args.file_path) > args.chunk_size:
            result, exec_time, mem_used = measure_performance(
                processor.process_large_file, args.file_path,
                chunk_size=args.chunk_size
            )
        else:
            result, exec_time, mem_used = measure_performance(
                processor.process_file, args.file_path
            )

        # 输出摘要
        stats = chunker.stats
        print(f"\n{'='*50}")
        print(f"  Regex Tokenizer - Processing Summary")
        print(f"{'='*50}")
        print(f"  Input:    {args.file_path}")
        print(f"  Output:   {args.output_file} ({args.output_format})")
        print(f"  Chunks:   {stats['total_chunks']}")
        print(f"  Tokens:   {stats['total_tokens']}")
        print(f"  Chars:    {stats['total_characters']}")
        print(f"  Lines:    {stats['total_lines']}")
        if stats['type_distribution']:
            print(f"\n  Type Distribution:")
            for t, c in sorted(stats['type_distribution'].items(),
                               key=lambda x: -x[1]):
                print(f"    {t:20s} {c:>6d}")
        print(f"\n  Time:     {exec_time:.3f}s")
        print(f"  Memory:   {format_bytes(mem_used)}")
        print(f"{'='*50}\n")

    except ExportError as e:
        logging.error(f"Export error: {e}")
        sys.exit(1)
    except TokenizerError as e:
        logging.error(f"Tokenizer error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
