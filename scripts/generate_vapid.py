from pywebpush import WebPusher

# Generating VAPID keys
try:
    # This generates a dictionary with 'privateKey', 'publicKey', and 'subject' usually, 
    # but pywebpush doesn't have a direct 'generate_keys' function exposed simply in all versions.
    # Actually, people often use `vapid --applicationServerKey` CLI or similar.
    # But let's use cryptography library if available, or just use a helper if pywebpush has one.
    
    # Or better, use ECPair from cryptography
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    import base64

    def int_to_bytes(i, length):
        return i.to_bytes(length, byteorder='big')

    def base64url_encode(data):
        return base64.urlsafe_b64encode(data).rstrip(b'=')

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # Get private key in integer format for some libs or PEM
    private_val = private_key.private_numbers().private_value
    private_bytes = int_to_bytes(private_val, 32)
    private_b64 = base64url_encode(private_bytes).decode('utf-8')

    # Get public key in uncompressed format
    numbers = public_key.public_numbers()
    public_bytes = b'\x04' + int_to_bytes(numbers.x, 32) + int_to_bytes(numbers.y, 32)
    public_b64 = base64url_encode(public_bytes).decode('utf-8')
    
    # Also save PEM for backend if it prefers that (the config had a .pem filename)
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open("f:/DD/backend/private_key.pem", "wb") as f:
        f.write(pem_private)

    print(f"VAPID_PRIVATE_KEY={private_b64}")  # This is the raw scalar often used in JS libs, but python usage varies. 
    # Actually backend config used a filename, so saving the file is good.
    # But it also had a public key string.
    
    print(f"VAPID_PUBLIC_KEY={public_b64}")

except ImportError:
    print("Cryptography module not found. Please install cryptography.")
except Exception as e:
    print(f"Error: {e}")
