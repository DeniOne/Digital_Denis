from py_vapid import Vapid
v = Vapid.from_file('private_key.pem')
print(dir(v))
if hasattr(v, 'public_key'):
    print("HAS PUBLIC KEY")
    import base64
    # Raw is usually 65 bytes for P-256 (0x04 + 32x + 32y)
    # Vapid expects raw bytes in some formats.
    # pywebpush / vapid usually handles it.
    pk = v.public_key
    if hasattr(pk, 'public_bytes'):
       # Cryptography object?
       from cryptography.hazmat.primitives import serialization
       print(pk.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint).hex())
    else:
       print('Type:', type(pk))
