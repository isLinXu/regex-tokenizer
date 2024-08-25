import os
import sys
import argparse

from tokenizer.regex_tokenizer import TextChunker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    parser.add_argument('output_file', type=str, help='Path to the output JSONL file', nargs='?', default='output.jsonl')
    parser.add_argument('--config', type=str, help='Path to the YAML config file', default='config.yaml')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker(config_file=args.config, output_file=args.output_file)
    chunker.process_text(args.file_path)