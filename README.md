



![logo1](https://github.com/user-attachments/assets/6b62a01f-19b8-4f7a-b229-7c960fcf0467)

![GitHub watchers](https://img.shields.io/github/watchers/isLinXu/regex-tokenizer.svg?style=social) ![GitHub stars](https://img.shields.io/github/stars/isLinXu/regex-tokenizer.svg?style=social) ![GitHub forks](https://img.shields.io/github/forks/isLinXu/regex-tokenizer.svg?style=social) ![GitHub followers](https://img.shields.io/github/followers/isLinXu.svg?style=social)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fatrox%2Fsync-dotenv%2Fbadge&style=flat)](https://github.com/isLinXu/regex-tokenizer)  ![img](https://badgen.net/badge/icon/learning?icon=deepscan&label)![GitHub repo size](https://img.shields.io/github/repo-size/isLinXu/regex-tokenizer.svg?style=flat-square) ![GitHub language count](https://img.shields.io/github/languages/count/isLinXu/regex-tokenizer)  ![GitHub last commit](https://img.shields.io/github/last-commit/isLinXu/regex-tokenizer) ![GitHub](https://img.shields.io/github/license/isLinXu/regex-tokenizer.svg?style=flat-square)![img](https://hits.dwyl.com/isLinXu/regex-tokenizer.svg)

---

# regex-tokenizer

Converted the [Jina Tokenizer regex pattern](https://gist.github.com/hanxiao/3f60354cf6dc5ac698bc9154163b4e6a) to python.

regex-tokenizer是一个用于将文本文件分块的工具。
它可以根据配置文件中的正则表达式模式将文本分割成不同的块，并生成统计信息。
该工具支持大文件处理、并行处理和多种输出格式。

## v3.0 更新

| 类别 | 改动 |
|------|------|
| **Bug 修复** | 双重处理导致统计翻倍 → 合并为单次处理路径 |
| **Bug 修复** | 大文件 `'w'` 模式覆盖数据 → 改为 `'a'` 追加模式 |
| **Bug 修复** | 边界截断硬切 → 语义边界感知分割（段落 > 换行 > 空格 > 硬切） |
| **Bug 修复** | CJK token 计数不准确 → 自动检测 CJK 比例，按字符计数 |
| **Bug 修复** | 超时保护无效 → 实现 SIGALRM (Unix) + 线程超时双策略 |
| **性能** | fullmatch 循环逐一匹配 → 命名捕获组单次 finditer（减少 ~95% 匹配次数） |
| **性能** | `re` 模块 → `regex` 模块（更好的 Unicode 支持） |
| **性能** | `num_threads` 参数已声明但未实现 → ThreadPoolExecutor 并行处理 |
| **架构** | `sys.exit(1)` 错误处理 → 自定义异常层级（ConfigError/PatternError/ExportError/TimeoutError） |
| **架构** | `patterns.json` 硬编码数字 → `patterns_new.json` 引用 config.yaml 占位符 + 命名捕获组 |
| **架构** | logger 重复添加 handler → 幂等 setup_logging + reset_logging |
| **质量** | 无测试 → 23 个单元测试覆盖核心模块 |

## v3.1 更新

| 类别 | 改动 |
|------|------|
| **功能** | 性能测量集成（执行时间 + 内存峰值） |
| **功能** | 输出摘要（Processing Summary） |
| **功能** | embedding-ready 输出格式（兼容 Chroma/FAISS/Milvus） |
| **功能** | Python API 编程接口（`chunk_text`/`chunk_file`/`quick_stats`） |
| **功能** | 模式热更新（`update_regex_patterns`/`reload_patterns`） |
| **质量** | 单元测试扩展至 34 个 |

## v3.2 更新

| 类别 | 改动 |
|------|------|
| **功能** | **Coverage 分析 & Gap 检测** — 对比原文与 chunk 拼接文本，找出未被匹配的"间隙" |
| **功能** | **Overlap 滑动窗口** — 相邻 chunk 添加重叠上下文，解决跨块语义断裂 |
| **功能** | **Streaming Iterator API** — 生成器接口逐块返回，避免大文件全量驻留内存 |
| **功能** | **Smart Chunk Merge** — 合并相邻同类型碎片块（如 hashtag/mention），拆分超大块 |
| **功能** | **Stdout NDJSON 流式输出** — 每行一个 JSON 对象，兼容 jq/yq，支持管道串联 |
| **功能** | **Benchmark 套件** — 标准语料量化测试（吞吐量/延迟/内存/覆盖率） |
| **配置** | 新增 `OVERLAP_CHARS`、`MIN_TOKEN_THRESHOLD` 参数 |
| **质量** | 单元测试扩展至 62 个（28 个 v3.2 新增） |

# 效果展示

|                             Text                             |                           Chunker                            |                            Jsonl                             |
| :----------------------------------------------------------: | :----------------------------------------------------------: | :----------------------------------------------------------: |
| <img width="746" alt="src1" src="https://github.com/user-attachments/assets/e9b11d5f-e8db-4cb6-8394-7d4acb52182e"> | <img width="928" alt="demo1@2x" src="https://github.com/user-attachments/assets/848ad51b-c032-4c38-8670-56e266bd7a3b"> | <img width="746" alt="result1@2x" src="https://github.com/user-attachments/assets/7923c7c6-dcd5-445a-a216-f43b663c82e2"> |
| <img width="746" alt="src2" src="https://github.com/user-attachments/assets/5fec3a7d-82a4-4bc8-92d7-23e8ba347b25"> | <img width="732" alt="demo2" src="https://github.com/user-attachments/assets/3cf97e15-8494-4d72-bcb4-c4c5a4f796b2"> | <img width="746" alt="result2@2x" src="https://github.com/user-attachments/assets/586d9df1-2a79-4614-83e7-871aa6c8d91d"> |
| <img width="746" alt="src3" src="https://github.com/user-attachments/assets/f5e8630f-68d1-4da3-9de3-fda69b76b061">                                                             | <img width="746" alt="demo3@2x" src="https://github.com/user-attachments/assets/b11ff8e4-e94c-40f2-9c11-8032be306ee6"> | <img width="746" alt="result3@2x" src="https://github.com/user-attachments/assets/d587f55b-66cf-406f-acea-4b7f62049704"> |
|  |                                                              |                                                              |

# 特性
- 配置驱动：通过 YAML 配置文件和 JSON 正则表达式文件进行配置。
- 多种输出格式：支持 JSONL、CSV、XML、Excel 和 embedding 格式的输出。
- 大文件处理：语义边界感知分割，避免截断破坏语义完整性。
- 并行处理：支持多线程并行处理（`--num_threads`），提高处理速度。
- CJK 友好：自动检测中日韩文本比例，切换字符级/词级 token 计数。
- 超时保护：SIGALRM (Unix) + 线程超时双策略，防止灾难性回溯。
- 性能测量：提供执行时间和内存使用情况的测量。
- 日志记录：幂等日志配置，同时输出到控制台和文件。
- 统计信息：生成详细统计，包括类型分布（type_distribution）。
- 异常体系：自定义异常层级替代 sys.exit，便于上层捕获和处理。
- **v3.2** Coverage 分析：检测正则匹配遗漏的文本区域（gap）。
- **v3.2** Overlap 窗口：相邻 chunk 添加重叠上下文，解决跨块语义断裂。
- **v3.2** 流式迭代器：生成器接口逐块返回，内存友好。
- **v3.2** 智能合并：合并相邻同类型碎片块，拆分超大块。
- **v3.2** NDJSON 流式输出：每行一个 JSON 对象，兼容 jq/yq。
- **v3.2** Benchmark 套件：标准语料量化测试。

# 用法

## 安装

```
git clone https://github.com/isLinXu/regex-tokenizer
cd  regex-tokenizer
```

```
pip install -r requirements.txt
```

## config
配置文件 `config.yaml` 包含了一些配置参数，如最大标题长度、最大标题内容长度等。
```yaml
MAX_HEADING_LENGTH: 7
MAX_HEADING_CONTENT_LENGTH: 200
MAX_HEADING_UNDERLINE_LENGTH: 200
```

## patterns
正则表达式文件 `patterns.json` 包含了各种正则表达式，如标题、引文、表格等。  
v3.0 推荐 `patterns_new.json`，支持 config.yaml 占位符引用和命名捕获组：
```json
{
  "headings": "(?:^(?:[#*=-]{1,{MAX_HEADING_LENGTH}}|...",
  "code_block": "(?:(?:^|\\r?\\n)(?:```|~~~)...",
  ...
}
```
占位符 `{MAX_HEADING_LENGTH}` 在加载时自动替换为 config.yaml 中的值。

## 运行

```shell
python3 run.py sample.txt --config config.yaml \
--regex patterns_new.json \
--output_file output.jsonl \
--output_format jsonl \
--num_threads 4 \
--stats_file stats.json
```

### v3.2 新增参数

```shell
# 智能合并碎片块
python3 run.py input.md out.jsonl --smart_merge

# 添加重叠上下文（50字符）
python3 run.py input.md out.jsonl --overlap_chars 50

# 覆盖率分析
python3 run.py input.md out.jsonl --coverage

# NDJSON 流式输出
python3 run.py input.md out.jsonl --ndjson_stream
```

### Python API (v3.2)

```python
from tokenizer.api import chunk_text, chunk_file

# 带智能合并
results = chunk_text("# Hello\nWorld.", smart_merge=True)

# 带重叠窗口
results = chunk_text("# Hello\nWorld.", overlap_chars=50)

# 带覆盖率分析
result = chunk_text("# Hello\nWorld.", coverage=True)
print(result['coverage']['coverage_ratio'])  # 0.95

# 流式迭代器
from tokenizer.streaming import StreamingChunker
streamer = StreamingChunker()
for chunk in streamer.chunk_text_iter(long_text):
    process(chunk)  # 逐块处理，内存友好

# NDJSON 流式输出
from tokenizer.ndjson_stream import NDJSONWriter
writer = NDJSONWriter(output_file='result.ndjson')
for chunk in chunks:
    writer.write(chunk)
writer.close()
```

## 测试

```shell
python -m pytest tests/ -v
```

```shell
python3 run.py data/demo/alice_in_wonderland.txt alice_in_wonderland.jsonl
```

```
python3 run.py data/demo/test.md test.jsonl
```

```
python3 run.py data/demo/红楼梦.txt 红楼梦.jsonl
```

日志文件 `text_chunker.log` 将记录所有的日志信息，包括错误和处理信息。

# 贡献

欢迎贡献代码！请 fork 本项目并提交 pull request。

# 致谢
本项目使用了 [Jina](https://github.com/jina-ai/jina) 的 Tokenizer 模块，
感谢 [hanxiao](https://github.com/hanxiao) 的贡献。

