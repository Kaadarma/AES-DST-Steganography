# AES + DST Steganography

## Overview

Project ini mengimplementasikan pengamanan data dengan menggabungkan enkripsi AES dan steganografi berbasis transform domain (DST). Pesan dienkripsi terlebih dahulu, kemudian disisipkan ke dalam gambar, dan dapat diekstrak kembali serta didekripsi.

---

## System Flow

Pesan → AES Encryption → DST → Embedding → Stego Image  
Stego Image → DST → Extraction → AES Decryption → Pesan Asli

---

## Core Methods

- AES digunakan untuk mengenkripsi pesan
- DST digunakan untuk mengubah gambar ke domain frekuensi
- QIM digunakan untuk menyisipkan bit ke dalam koefisien

---

## Evaluation

Kualitas gambar diukur menggunakan:
- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index)

---

# Project Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- git (optional)

---

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd <project-directory>