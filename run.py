"""Regex Tokenizer 入口脚本 - v3.2

修复：合并双路径为单次处理路径，避免统计翻倍
v3.1: 集成性能测量、输出摘要、embedding 格式
v3.2: Coverage 分析、Overlap 窗口、Smart Merge、NDJSON 流式输出
"""

import argparse
import os
import sys
import logging

from tokenizer.processor import TextProcessor
from tokenizer.regex_tokenizer import TextChunker
from tokenizer.performance_measurer import measure_performance, format_bytes
from tokenizer.coverage import CoverageAnalyzer
from tokenizer.overlap import OverlapSlidingWindow
from tokenizer.smart_merge import SmartChunkMerger
from tokenizer.ndjson_stream import NDJSONWriter
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
  python run.py input.md out.jsonl --smart_merge
  python run.py input.md out.jsonl --overlap_chars 50
  python run.py input.md out.jsonl --coverage
  python run.py input.md out.jsonl --ndjson_stream
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
    # v3.2 新增参数
    parser.add_argument('--smart_merge', action='store_true',
                        help='Enable smart chunk merge (v3.2)')
    parser.add_argument('--overlap_chars', type=int, default=0,
                        help='Overlap characters between adjacent chunks (v3.2)')
    parser.add_argument('--coverage', action='store_true',
                        help='Enable coverage analysis & gap detection (v3.2)')
    parser.add_argument('--ndjson_stream', action='store_true',
                        help='Enable NDJSON streaming output (v3.2)')
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

        # 获取 chunks
        chunks = chunker.stats.get('chunk_details', [])

        # v3.2: 智能合并
        if args.smart_merge:
            merger = SmartChunkMerger()
            chunks = merger.merge(chunks)

        # v3.2: 重叠窗口
        if args.overlap_chars > 0:
            window = OverlapSlidingWindow(overlap_chars=args.overlap_chars)
            chunks = window.apply(chunks)

        # v3.2: NDJSON 流式输出
        if args.ndjson_stream:
            writer = NDJSONWriter(
                output_file=args.output_file.replace('.jsonl', '.ndjson')
            )
            for chunk in chunks:
                writer.write(chunk)
            writer.close()

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

        # v3.2: 覆盖率分析
        if args.coverage:
            with open(args.file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            analyzer = CoverageAnalyzer(chunker)
            coverage_report = analyzer.analyze(text, chunks)
            print(f"\n  Coverage Analysis:")
            print(f"    Coverage:  {coverage_report['coverage_ratio']*100:.1f}%")
            print(f"    Gaps:     {coverage_report['gap_count']}")
            if coverage_report['gaps']:
                for gap in coverage_report['gaps'][:5]:
                    preview = gap['text'][:50].replace('\n', '\\n')
                    print(f"      [{gap['start']}:{gap['end']}] len={gap['length']} \"{preview}...\"")

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
