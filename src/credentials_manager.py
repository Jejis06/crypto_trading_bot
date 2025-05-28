import os
import json
from cryptography.fernet import Fernet

class CredentialsManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.cred_file = os.path.join(self.config_dir, 'credentials.enc')
        self.key_file = os.path.join(self.config_dir, '.key')
        
        # Ensure config directory exists
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Initialize or load encryption key
        self._init_encryption()

    def _init_encryption(self):
        """Initialize or load the encryption key."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)

    def save_credentials(self, api_key, api_secret):
        """Save API credentials encrypted."""
        data = {
            'api_key': api_key,
            'api_secret': api_secret
        }
        encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
        
        with open(self.cred_file, 'wb') as f:
            f.write(encrypted_data)

    def load_credentials(self):
        """Load saved API credentials."""
        if not os.path.exists(self.cred_file):
            return None, None
        
        try:
            with open(self.cred_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())
            
            return data['api_key'], data['api_secret']
        except Exception:
            return None, None 