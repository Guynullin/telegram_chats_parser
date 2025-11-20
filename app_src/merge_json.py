import os
import json
from datetime import datetime
from pathlib import Path
from .utils import setup_logger

logger = setup_logger('merge_json')

def merge_json_files(input_dir, output_dir):
    all_entries = []
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_entries.extend(data)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Error reading file {file_path}: {e}")
    
    current_date = datetime.now().strftime("%d-%m-%Y")
    base_filename = f"merged-{current_date}.json"
    output_path = Path(output_dir) / base_filename
    
    if output_path.exists():
        current_time = datetime.now().strftime("%H-%M")
        base_filename = f"merged-{current_date}-{current_time}.json"
        output_path = Path(output_dir) / base_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Combined {len(all_entries)} entries in the {output_path}")