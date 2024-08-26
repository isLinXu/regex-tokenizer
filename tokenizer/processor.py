import logging
from .result_saver import save_results, save_stats
from .performance_measurer import measure_performance, format_bytes


class TextProcessor:
    def __init__(self, chunker, output_file='output.jsonl', stats_file='stats.json'):
        self.chunker = chunker
        self.output_file = output_file
        self.stats_file = stats_file

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        chunks = self.chunker.chunk_text(text)
        self.save_results(chunks)
        self.save_stats()

    def process_large_file(self, file_path, chunk_size=1024 * 1024):
        with open(file_path, 'r', encoding='utf-8') as file:
            while True:
                text_chunk = file.read(chunk_size)
                if not text_chunk:
                    break
                chunks = self.chunker.chunk_text(text_chunk)
                self.save_results(chunks)
        self.save_stats()

    def process_text_in_parallel_with_performance(self, text, num_threads=4):
        from concurrent.futures import ThreadPoolExecutor

        def chunk_and_process(sub_text):
            return self.chunker.chunk_text(sub_text)

        text_chunks = [text[i:i + len(text) // num_threads] for i in range(0, len(text), len(text) // num_threads)]
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            results, execution_time, memory_used = measure_performance(executor.map, chunk_and_process, text_chunks)

        matches = [item for sublist in results for item in sublist]
        return matches, execution_time, memory_used

    def save_results(self, matches, output_format='jsonl'):
        save_results(matches, self.output_file, output_format)

    def save_stats(self):
        save_stats(self.chunker.stats, self.stats_file)

    def print_results(self, matches, execution_time, memory_used):
        logging.info(f"Total chunks: {self.chunker.stats['total_chunks']}")
        logging.info(f"Total tokens: {self.chunker.stats['total_tokens']}")
        logging.info(f"Total characters: {self.chunker.stats['total_characters']}")
        logging.info(f"Total lines: {self.chunker.stats['total_lines']}")
        logging.info(f"Execution time: {execution_time:.2f} seconds")
        logging.info(f"Memory used: {format_bytes(memory_used)}")

        logging.info('\nFirst 10 chunks:')
        if matches:
            for match in matches[:10]:
                logging.info(repr(match)[:50])
        else:
            logging.info('No chunks found.')

        logging.info(f"\nRegex flags: {self.chunker.chunk_regex.flags}")

        if execution_time > 5:
            logging.warning('Execution time exceeded 5 seconds. The regex might be too complex or the input too large.')
        if memory_used > 100 * 1024 * 1024:
            logging.warning('Memory usage exceeded 100 MB. Consider processing the input in smaller chunks.')