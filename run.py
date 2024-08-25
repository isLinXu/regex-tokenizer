import logging
import os
import sys
import argparse

from tokenizer.regex_tokenizer import TextChunker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output file', nargs='?',
                            default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
    parser.add_argument('--regex', type=str, help='Path to the JSON regex config file', default='patterns.json')
    parser.add_argument('--chunk_size', type=int, help='Chunk size for processing large files', default=1024 * 1024)
    parser.add_argument('--output_format', type=str, help='Output format (jsonl, csv, xml)', default='jsonl')
    parser.add_argument('--num_threads', type=int, help='Number of threads for parallel processing', default=4)
    parser.add_argument('--stats_file', type=str, help='Path to the output statistics file', default='stats.json')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        logging.error(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(config_file=args.config, regex_file=args.regex, output_file=args.output_file,
                              stats_file=args.stats_file)

    try:
        if os.path.getsize(args.file_path) > args.chunk_size:
            chunker.process_large_file(args.file_path, chunk_size=args.chunk_size)
        else:
            chunker.process_file(args.file_path)

        with open(args.file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        matches = chunker.process_text_in_parallel(text, num_threads=args.num_threads)
        chunker.print_results(matches, 0,0)  # Execution time and memory usage are not calculated here for simplicity
        chunker.save_results(matches, output_format=args.output_format)
        chunker.save_stats()
    except Exception as e:
        logging.error(f"Error in main execution: {e}")