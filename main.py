import numpy as np
import hashlib, struct

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

from scipy.fft import dstn, idstn
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim


class AESCipher:
    def __init__(self, password):
        self.key = hashlib.sha256(password.encode()).digest()

    def encrypt(self, text):
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(pad(text.encode(), AES.block_size))

    def decrypt(self, data):
        if len(data) < 16:
            raise ValueError("Data terlalu pendek")
        iv = data[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(data[16:]), AES.block_size).decode()


class StegoDST:
    def __init__(self, step=25.0):
        self.step  = step
        self.block = 8

    def to_bits(self, data):
        return [int(b) for byte in data for b in f"{byte:08b}"]

    def to_bytes(self, bits):
        return bytes(
            int("".join(map(str, bits[i:i+8])), 2)
            for i in range(0, len(bits), 8)
        )

    def _get_blocks(self, ch):
        blocks = []
        for i in range(0, ch.shape[0] - self.block + 1, self.block):
            for j in range(0, ch.shape[1] - self.block + 1, self.block):
                blocks.append((i, j))
        return blocks

    def _embed_bit(self, coeff, bit):
        q = round(coeff / self.step)
        if bit == 1 and q % 2 == 0:
            q += 1
        elif bit == 0 and q % 2 == 1:
            q += 1
        return q * self.step

    def _extract_bit(self, coeff):
        return round(coeff / self.step) % 2

    def get_capacity(self, img):
        h, w     = img.shape[:2]
        n_blocks = (h // 8) * (w // 8)
        return (n_blocks - 32) // 8

    def embed(self, img, data):
        img = img.copy().astype(float)
        ch  = img[:, :, 2].copy()

        blocks      = self._get_blocks(ch)
        header_bits = self.to_bits(struct.pack(">I", len(data)))
        data_bits   = self.to_bits(data)
        all_bits    = header_bits + data_bits

        if len(all_bits) > len(blocks):
            raise ValueError("Pesan terlalu besar untuk gambar ini!")

        for k, bit in enumerate(all_bits):
            i, j    = blocks[k]
            block   = ch[i:i+self.block, j:j+self.block]
            d       = dstn(block, norm='ortho')
            d[3, 4] = self._embed_bit(d[3, 4], bit)
            ch[i:i+self.block, j:j+self.block] = idstn(d, norm='ortho')

        img[:, :, 2] = np.clip(ch, 0, 255)
        return img.astype(np.uint8)

    def extract(self, img):
        ch     = img[:, :, 2].astype(float)
        blocks = self._get_blocks(ch)

        header_bits = []
        for k in range(32):
            i, j  = blocks[k]
            d     = dstn(ch[i:i+self.block, j:j+self.block], norm='ortho')
            header_bits.append(self._extract_bit(d[3, 4]))

        length = int("".join(map(str, header_bits)), 2)

        if length <= 0 or length > 50000:
            raise ValueError("Header rusak! Pastikan password benar dan gambar adalah stego-image.")

        data_bits = []
        for k in range(32, 32 + length * 8):
            i, j  = blocks[k]
            d     = dstn(ch[i:i+self.block, j:j+self.block], norm='ortho')
            data_bits.append(self._extract_bit(d[3, 4]))

        return self.to_bytes(data_bits)


def evaluate(original, stego):
    psnr_val = psnr(original, stego, data_range=255)
    ssim_val = ssim(original, stego, channel_axis=2, data_range=255)
    return psnr_val, ssim_val