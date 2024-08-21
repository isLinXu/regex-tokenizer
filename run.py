import os
import sys
import argparse

from tokenizer.regex_tokenizer import TextChunker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chunk text file.')
    parser.add_argument('file_path', type=str, help='Path to the text file')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    chunker = TextChunker()
    chunker.process_text(args.file_path)