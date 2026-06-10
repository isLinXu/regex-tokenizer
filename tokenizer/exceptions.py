"""自定义异常层级，替代 sys.exit()"""


class TokenizerError(Exception):
    """基础异常类"""


class ConfigError(TokenizerError):
    """配置加载失败时抛出"""


class PatternError(TokenizerError):
    """正则模式编译失败时抛出"""


class ExportError(TokenizerError):
    """导出失败时抛出"""


class TimeoutError(TokenizerError):
    """正则匹配超时时抛出"""
