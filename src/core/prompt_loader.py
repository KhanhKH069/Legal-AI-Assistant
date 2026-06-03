import os
import yaml
from typing import Dict
_PROMPTS: Dict[str, str] = {}

def load_prompts():
    global _PROMPTS
    if _PROMPTS:
        return
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'prompts.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _PROMPTS = yaml.safe_load(f)
    except Exception as e:
        print(f'Lỗi khi load prompts.yaml: {e}')
        _PROMPTS = {}

def get_prompt(agent_name: str, default: str='') -> str:
    load_prompts()
    return _PROMPTS.get(agent_name, default)