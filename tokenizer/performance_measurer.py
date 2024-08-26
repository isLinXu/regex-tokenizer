import time
import psutil
import os

def measure_performance(func, *args, **kwargs):
    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss

    result = func(*args, **kwargs)

    end_time = time.time()
    end_memory = process.memory_info().rss

    execution_time = end_time - start_time
    memory_used = end_memory -start_memory

    return result, execution_time, memory_used

def format_bytes(size):
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0