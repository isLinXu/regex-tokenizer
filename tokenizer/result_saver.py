import json
import csv
import hashlib
import logging
import pandas as pd
from xml.etree.ElementTree import Element, SubElement, ElementTree

from .exceptions import ExportError


def _chunk_id(text, index, source_file=""):
    """生成确定性 chunk ID（基于内容哈希 + 序号）"""
    content = f"{source_file}:{index}:{text[:200]}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def save_results(matches, output_file, output_format='jsonl', source_file=""):
    if output_format == 'jsonl':
        save_results_to_jsonl(matches, output_file)
    elif output_format == 'csv':
        save_results_to_csv(matches, output_file)
    elif output_format == 'xml':
        save_results_to_xml(matches, output_file)
    elif output_format == 'excel':
        save_results_to_excel(matches, output_file)
    elif output_format == 'embedding':
        save_results_to_embedding(matches, output_file, source_file=source_file)
    else:
        raise ExportError(f"Unsupported output format: {output_format}")

def save_results_to_jsonl(matches, output_file):
    """将匹配结果保存为JSONL格式，逐行追加写入"""
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            for match in matches:
                json.dump(match, f, ensure_ascii=False)
                f.write('\n')
        logging.info(f"Results saved to {output_file}")
    except IOError as e:
        raise ExportError(f"Error writing to file {output_file}: {e}")

def save_results_to_csv(matches, output_file):
    csv_file = output_file.replace('.jsonl', '.csv')
    try:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['text', 'type', 'token_count'])
            writer.writeheader()
            for match in matches:
                writer.writerow(match)
        logging.info(f"Results saved to {csv_file}")
    except IOError as e:
        raise ExportError(f"Error writing to file {csv_file}: {e}")

def save_results_to_xml(matches, output_file):
    root = Element('chunks')
    for match in matches:
        chunk_elem = SubElement(root, 'chunk')
        text_elem = SubElement(chunk_elem, 'text')
        text_elem.text = match['text']
        type_elem = SubElement(chunk_elem, 'type')
        type_elem.text = match['type']
        token_elem = SubElement(chunk_elem, 'token_count')
        token_elem.text = str(match['token_count'])
    tree = ElementTree(root)
    xml_file = output_file.replace('.jsonl', '.xml')
    try:
        tree.write(xml_file, encoding='utf-8')
        logging.info(f"Results saved to {xml_file}")
    except IOError as e:
        raise ExportError(f"Error writing to file {xml_file}: {e}")

def save_results_to_excel(matches, output_file):
    excel_file = output_file.replace('.jsonl', '.xlsx')
    try:
        df = pd.DataFrame(matches)
        df.to_excel(excel_file, index=False)
        logging.info(f"Results saved to {excel_file}")
    except IOError as e:
        raise ExportError(f"Error writing to file {excel_file}: {e}")

def save_stats(stats, stats_file):
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logging.info(f"Statistics saved to {stats_file}")
    except IOError as e:
        raise ExportError(f"Error writing stats to {stats_file}: {e}")


def save_results_to_embedding(matches, output_file, source_file=""):
    """导出为 embedding-ready 格式，兼容 Chroma / FAISS / Milvus。

    每行一个 JSON 对象：
    {
      "id": "a1b2c3d4e5f6g7h8",
      "text": "chunk content...",
      "metadata": {
        "type": "headings",
        "token_count": 12,
        "character_count": 45,
        "line_count": 1,
        "source": "doc.md"
      }
    }
    """
    embed_file = output_file.replace('.jsonl', '.embedding.jsonl')
    try:
        with open(embed_file, 'w', encoding='utf-8') as f:
            for idx, match in enumerate(matches):
                record = {
                    'id': _chunk_id(match.get('text', ''), idx, source_file),
                    'text': match.get('text', ''),
                    'metadata': {
                        'type': match.get('type', 'unknown'),
                        'token_count': match.get('token_count', 0),
                        'character_count': match.get('character_count', len(match.get('text', ''))),
                        'line_count': match.get('line_count', 1),
                        'source': source_file,
                    }
                }
                json.dump(record, f, ensure_ascii=False)
                f.write('\n')
        logging.info(f"Embedding-ready results saved to {embed_file}")
    except IOError as e:
        raise ExportError(f"Error writing embedding file {embed_file}: {e}")