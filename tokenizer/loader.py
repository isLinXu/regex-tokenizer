import yaml
import json
import logging
import sys

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML config file: {e}")
        sys.exit(1)



def load_and_substitute_regex_patterns(regex_file, config):
    try:
        with open(regex_file, 'r') as file:
            patterns = json.load(file)
    except FileNotFoundError:
        logging.error(f"Regex file not found: {regex_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON regex file: {e}")
        sys.exit(1)

    # Substitute placeholders with config values
    for key, pattern in patterns.items():
        for config_key, config_value in config.items():
            placeholder = f"{{{config_key}}}"
            pattern = pattern.replace(placeholder, str(config_value))
        patterns[key] = pattern

    return patterns
