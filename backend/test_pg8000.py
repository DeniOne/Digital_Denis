
import pg8000.native
import sys

# Connection details
user = "denis"
password = "denis_dev_2024"
host = "localhost"
port = 5432
database = "digital_denis"

print(f"Testing connection with pg8000 to {database}...")

try:
    con = pg8000.native.Connection(user, host=host, port=port, database=database, password=password)
    print("Connection successful!")
    
    result = con.run("SELECT 1")
    print(f"Query result: {result}")
    
    con.close()
except Exception as e:
    print(f"Connection failed: {e}")
    import traceback
    traceback.print_exc()
