"""配置与正则模式加载器

使用自定义异常替代 sys.exit，提供更清晰的错误处理。
"""

import yaml
import json
import logging
import sys

# 导入自定义异常层级
from .exceptions import (
    TokenizerError,      # 基础异常
    ConfigError,         # 配置加载失败
    PatternError,        # 正则模式编译失败
    ExportError,         # 导出失败
    TimeoutError,        # 超时
)


def load_config(config_file):
    """加载 YAML 配置文件。

    抛出 ConfigError 而非 sys.exit(1)。
    """
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {config_file}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML: {e}")


def load_and_substitute_regex_patterns(regex_file, config):
    """加载正则模式 JSON 文件并替换占位符。

    抛出 PatternError 而非 sys.exit(1)。
    """
    try:
        with open(regex_file, 'r') as file:
            patterns = json.load(file)
    except FileNotFoundError:
        raise PatternError(f"Regex file not found: {regex_file}")
    except json.JSONDecodeError as e:
        raise PatternError(f"Error parsing regex file: {e}")

    # Substitute placeholders with config values
    for key, pattern in patterns.items():
        for config_key, config_value in config.items():
            placeholder = f"{{{config_key}}}"
            pattern = pattern.replace(placeholder, str(config_value))
        patterns[key] = pattern

    return patterns
