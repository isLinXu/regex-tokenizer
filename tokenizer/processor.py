import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil

from tokenizer.utils import measure_performance, print_results, save_results, save_stats


def process_text(chunk_text, chunk_regex, text, output_file, stats_file, stats):
    try:
        matches, execution_time, memory_used = measure_performance(chunk_text, text)
        print_results(matches, execution_time, chunk_regex, memory_used)
        save_results(matches, output_file)
        save_stats(stats_file, stats)
    except Exception as e:
        logging.error(f"Error processing text: {e}")


def process_file(file_path, chunk_text, chunk_regex, output_file, stats_file, stats):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        process_text(chunk_text, chunk_regex, text, output_file, stats_file, stats)
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")


def process_large_file(file_path, chunk_size=1024 * 1024):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = []
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                text.append(chunk)
                if len(text) > 0:
                    process_text(''.join(text))
                    text = []
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")


def process_text_in_parallel(text, chunk_text, num_threads=4):
    chunk_size = len(text) // num_threads
    futures = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            start = i * chunk_size
            end = None if i == num_threads - 1 else (i + 1) * chunk_size
            futures.append(executor.submit(chunk_text, text[start:end]))

        all_matches = []
        for future in as_completed(futures):
            try:
                all_matches.extend(future.result())
            except Exception as e:
                logging.error(f"Error in thread execution: {e}")

    return all_matches


def process_text_in_parallel_with_performance(text, num_threads=4):
    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss

    matches = process_text_in_parallel(text, num_threads)

    end_time = time.time()
    end_memory = process.memory_info().rss

    execution_time = end_time - start_time
    memory_used = end_memory - start_memory

    return matches, execution_time, memory_used
