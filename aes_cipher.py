from Cryptodome.Cipher import AES

class Cipher:
    def __init__(self, key, nonce):
        self.key = key
        self.nonce = nonce

    def aes_encrypt(self, plaintext_bytes):
        cipher = AES.new(self.key, AES.MODE_CTR, nonce=self.nonce)
        return cipher.encrypt(plaintext_bytes)

    def aes_decrypt(self, ciphertext_bytes):
        cipher = AES.new(self.key, AES.MODE_CTR, nonce=self.nonce)
        return cipher.decrypt(ciphertext_bytes).decode("utf-8")