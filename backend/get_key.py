from py_vapid import Vapid
v = Vapid.from_file('private_key.pem')
# Vapid.public_key is usually raw bytes or similar?
# Using 'vapid' lib:
print(v.application_server_key)
