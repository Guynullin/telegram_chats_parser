import yaml
import logging
import os

from config import CYAML_PATH

def load_config():
    with open(CYAML_PATH, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name):
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(f'logs/app.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger