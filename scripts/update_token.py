import os
import re

env_path = r'f:\DD\.env'
token = '8046067739:AAE5zmXc0zEuhyLnLBn4NU5HiU-gDYEGc-Q'
key = 'TELEGRAM_BOT_TOKEN'

try:
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if key exists
        pattern = f'^{key}=.*'
        if re.search(pattern, content, re.MULTILINE):
            # Replace
            new_content = re.sub(pattern, f'{key}={token}', content, flags=re.MULTILINE)
            print(f"Updating existing {key}...")
        else:
            # Append
            new_content = content + f'\n{key}={token}\n'
            print(f"Appending new {key}...")
            
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: .env updated.")
    else:
        print(f"Error: {env_path} not found.")

except Exception as e:
    print(f"Error: {e}")
