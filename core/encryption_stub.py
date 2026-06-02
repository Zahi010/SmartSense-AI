# encryption_stub.py

import json
from cryptography.fernet import Fernet


class EncryptionStub:

    def __init__(self):
        import os
        key_path = "secret.key"
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                self.key = f.read().strip()
        else:
            self.key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(self.key)
        self.cipher = Fernet(self.key)

    def encrypt(self, data):
        """
        Encrypt a Python dictionary.
        Returns encrypted bytes.
        """
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted

    def decrypt(self, encrypted_data):
        """
        Decrypt encrypted bytes back to dictionary.
        """
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted.decode())