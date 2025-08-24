import os
from pathlib import Path

def load_env_file(env_file_path):
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())



def load_environment():
    base_dir = Path(__file__).resolve().parent.parent
    
    env_file = base_dir / '.env.local'
    
    if os.getenv('DJANGO_ENV') == 'production' or not os.getenv('DEBUG', '').lower() == 'true':
        env_file = base_dir / '.env'
    
    load_env_file(env_file)