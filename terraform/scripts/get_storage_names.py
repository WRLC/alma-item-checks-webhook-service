import re
import json
import os

config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'alma_item_checks_webhook_service', 'config.py')

with open(config_path, 'r') as f:
    content = f.read()

config_values = {
    'barcode_retrieval_queue': re.search(r'BARCODE_RETRIEVAL_QUEUE[^,]+,\s*"([^"]+)"', content).group(1),
    'item_validation_queue': re.search(r'ITEM_VALIDATION_QUEUE[^,]+,\s*"([^"]+)"', content).group(1),
    'item_validation_container': re.search(r'ITEM_VALIDATION_CONTAINER[^,]+,\s*"([^"]+)"', content).group(1)
}

print(json.dumps(config_values))
