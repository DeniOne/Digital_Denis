
import psycopg2
import sys
import os

# Inspect Env
print("Environment variables starting with PG:")
for k, v in os.environ.items():
    if k.startswith("PG"):
        print(f"{k}={v}")

dsn = "postgresql://denis:denis_dev_2024@localhost:5432/digital_denis"

try:
    # Try forcing client encoding in options if possible, 
    # but initially just try raw connect again to confirm env didn't change
    print(f"Connecting to: {dsn}")
    conn = psycopg2.connect(dsn, options="-c client_encoding=utf8")
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    # import traceback
    # traceback.print_exc()
