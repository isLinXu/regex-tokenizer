"""日志配置模块

支持同时输出到控制台和文件，防止重复添加 handler。
"""

import logging
import sys

_initialized = False


def setup_logging(log_file='text_chunker.log', level=logging.INFO):
    """配置全局日志。

    仅首次调用时生效，后续调用为空操作（幂等）。
    """
    global _initialized
    if _initialized:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    fmt = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台 handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    # 文件 handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        root_logger.addHandler(file_handler)
    except IOError as e:
        root_logger.warning("Could not create log file %s: %s", log_file, e)

    _initialized = True


def reset_logging():
    """重置日志状态（主要用于测试）"""
    global _initialized
    _initialized = False
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
