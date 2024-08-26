



![logo1](https://github.com/user-attachments/assets/6b62a01f-19b8-4f7a-b229-7c960fcf0467)

![GitHub watchers](https://img.shields.io/github/watchers/isLinXu/regex-tokenizer.svg?style=social) ![GitHub stars](https://img.shields.io/github/stars/isLinXu/regex-tokenizer.svg?style=social) ![GitHub forks](https://img.shields.io/github/forks/isLinXu/regex-tokenizer.svg?style=social) ![GitHub followers](https://img.shields.io/github/followers/isLinXu.svg?style=social)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fatrox%2Fsync-dotenv%2Fbadge&style=flat)](https://github.com/isLinXu/regex-tokenizer)  ![img](https://badgen.net/badge/icon/learning?icon=deepscan&label)![GitHub repo size](https://img.shields.io/github/repo-size/isLinXu/regex-tokenizer.svg?style=flat-square) ![GitHub language count](https://img.shields.io/github/languages/count/isLinXu/regex-tokenizer)  ![GitHub last commit](https://img.shields.io/github/last-commit/isLinXu/regex-tokenizer) ![GitHub](https://img.shields.io/github/license/isLinXu/regex-tokenizer.svg?style=flat-square)![img](https://hits.dwyl.com/isLinXu/regex-tokenizer.svg)

---

# regex-tokenizer

Converted the [Jina Tokenizer regex pattern](https://gist.github.com/hanxiao/3f60354cf6dc5ac698bc9154163b4e6a) to python.

regex-tokenizer是一个用于将文本文件分块的工具。
它可以根据配置文件中的正则表达式模式将文本分割成不同的块，并生成统计信息。
该工具支持大文件处理、并行处理和多种输出格式。

# 效果展示

|                             Text                             |                           Chunker                            |                            Jsonl                             |
| :----------------------------------------------------------: | :----------------------------------------------------------: | :----------------------------------------------------------: |
| <img width="746" alt="src1" src="https://github.com/user-attachments/assets/e9b11d5f-e8db-4cb6-8394-7d4acb52182e"> | <img width="928" alt="demo1@2x" src="https://github.com/user-attachments/assets/848ad51b-c032-4c38-8670-56e266bd7a3b"> | <img width="746" alt="result1@2x" src="https://github.com/user-attachments/assets/7923c7c6-dcd5-445a-a216-f43b663c82e2"> |
| <img width="746" alt="src2" src="https://github.com/user-attachments/assets/5fec3a7d-82a4-4bc8-92d7-23e8ba347b25"> | <img width="732" alt="demo2" src="https://github.com/user-attachments/assets/3cf97e15-8494-4d72-bcb4-c4c5a4f796b2"> | <img width="746" alt="result2@2x" src="https://github.com/user-attachments/assets/586d9df1-2a79-4614-83e7-871aa6c8d91d"> |
| <img width="746" alt="src3" src="https://github.com/user-attachments/assets/f5e8630f-68d1-4da3-9de3-fda69b76b061">                                                             | <img width="746" alt="demo3@2x" src="https://github.com/user-attachments/assets/b11ff8e4-e94c-40f2-9c11-8032be306ee6"> | <img width="746" alt="result3@2x" src="https://github.com/user-attachments/assets/d587f55b-66cf-406f-acea-4b7f62049704"> |
|  |                                                              |                                                              |

# 特性
- 配置驱动：通过 YAML 配置文件和 JSON 正则表达式文件进行配置。
- 多种输出格式：支持 JSONL、CSV、XML 和 Excel 格式的输出。
- 大文件处理：支持按块读取大文件，避免内存溢出。
- 并行处理：支持多线程并行处理，提高处理速度。
- 性能测量：提供执行时间和内存使用情况的测量。
- 日志记录：记录详细的日志信息，包括错误和处理信息。
- 统计信息：生成详细的统计信息，包括总块数、总字符数、总行数等。

# 用法

## 安装

```
git clone https://github.com/yourusername/text-chunker.git
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
... ...
```

## patterns
正则表达式文件 `patterns.json` 包含了各种正则表达式，如标题、引文、表格等。例如：
```json
{
  "headings": "(?:^(?:[#*=-]{1,7}|\\w[^\\r\\n]{0,200}\\r?\\n[-=]{2,200}|<h[1-6][^>]{0,100}>)[^\\r\\n]{1,200}(?:</h[1-6]>)?(?:\\r?\\n|$))",
  "citations": "(?:\\$[0-9]+\\$[^\\r\\n]{1,800})",
  ... ...
}
```

## 运行

```shell
python3 run.py sample.txt --config config.yaml \ 
													--regex patterns.json \
													--output_file output.jsonl 
													--output_format jsonl \
													--num_threads 4 \
													--stats_file stats.json
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

