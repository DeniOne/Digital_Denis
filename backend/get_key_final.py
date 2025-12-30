from py_vapid import Vapid
import base64
from cryptography.hazmat.primitives import serialization

v = Vapid.from_file('private_key.pem')
pub_bytes = v.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
print(base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('='))
