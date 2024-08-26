import json
import csv
import logging
import pandas as pd
from xml.etree.ElementTree import Element, SubElement, ElementTree

def save_results(matches, output_file, output_format='jsonl'):
    if output_format == 'jsonl':
        save_results_to_jsonl(matches, output_file)
    elif output_format == 'csv':
        save_results_to_csv(matches, output_file)
    elif output_format == 'xml':
        save_results_to_xml(matches, output_file)
    elif output_format == 'excel':
        save_results_to_excel(matches, output_file)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

def save_results_to_jsonl(matches, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for match in matches:
                json.dump(match, f, ensure_ascii=False)
                f.write('\n')
        logging.info(f"Results saved to {output_file}")
    except IOError as e:
        logging.error(f"Error writing to file {output_file}: {e}")

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
        logging.error(f"Error writing to file {csv_file}: {e}")

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
        logging.error(f"Error writing to file {xml_file}: {e}")

def save_results_to_excel(matches, output_file):
    excel_file = output_file.replace('.jsonl', '.xlsx')
    try:
        df = pd.DataFrame(matches)
        df.to_excel(excel_file, index=False)
        logging.info(f"Results saved to {excel_file}")
    except IOError as e:
        logging.error(f"Error writing to file {excel_file}: {e}")

def save_stats(stats, stats_file):
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logging.info(f"Statistics saved to {stats_file}")
    except IOError as e:
        logging.error(f"Error writing to file {stats_file}: {e}")