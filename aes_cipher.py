from Crypto.Cipher import AES

# AES Key and Nonce (must be 16 bytes each for AES-128)
AES_KEY = b'ThisIsASecretKey'
AES_NONCE = b'ThisIsASecretN'

class Cipher:
    def __init__(self, key=AES_KEY, nonce=AES_NONCE):
        self.key = key
        self.nonce = nonce

    def aes_encrypt(self, txt):
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=self.nonce)
        ciphertext, tag = cipher.encrypt_and_digest(txt)
        return ciphertext

    def aes_decrypt(self, cipher_text):
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=self.nonce)
        msg = cipher.decrypt(cipher_text)
        return msg.decode('utf-8')
