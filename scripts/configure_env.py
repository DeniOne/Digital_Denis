"""
Script to configure .env file with correct values.
"""
import os
from pathlib import Path

def update_env():
    env_path = Path(__file__).parent.parent / ".env"
    
    # Values to update
    updates = {
        "DATABASE_URL": "postgresql://denis:denis_dev_2024@localhost:5434/digital_denis",
        "OPENROUTER_API_KEY": "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",
        "ALLOWED_TELEGRAM_IDS": "441610858",
        "GOOGLE_CLIENT_ID": "your_client_id_here.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "your_client_secret_here",
    }
    
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}")
        return
    
    # Read current content
    content = env_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    # Update each key
    for key, value in updates.items():
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                print(f"Updated {key}")
                break
        
        if not found:
            lines.append(f"{key}={value}")
            print(f"Added {key}")
    
    # Write back
    env_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ .env updated successfully!")

if __name__ == "__main__":
    update_env()
