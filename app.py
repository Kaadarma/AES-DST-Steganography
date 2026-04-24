import streamlit as st
import numpy as np
from PIL import Image
import io

from main import AESCipher, StegoDST, evaluate


st.set_page_config(
    page_title="Steganografi AES + DST",
    page_icon="🔐",
    layout="wide"
)

st.title("Steganografi Gambar")
st.caption("Metode: AES-256 Encryption + DST (Discrete Sine Transform)")

tab_embed, tab_extract = st.tabs(["Embed (Sembunyikan Pesan)", "Extract (Ambil Pesan)"])


# TAB EMBED
with tab_embed:
    st.subheader("Sembunyikan Pesan ke dalam Gambar")

    col1, col2 = st.columns(2)

    with col1:
        uploaded = st.file_uploader(
            "Upload Gambar Cover",
            type=["jpg", "jpeg", "png"],
            key="embed_upload"
        )
        if uploaded:
            cover_img = np.array(Image.open(uploaded).convert("RGB"))
            st.image(cover_img, caption="Gambar Cover", use_container_width=True)

            stego     = StegoDST(step=25.0)
            kapasitas = stego.get_capacity(cover_img)
            st.info(f"Kapasitas gambar: **{kapasitas} bytes**")

    with col2:
        message  = st.text_area("Pesan Rahasia", placeholder="Ketik pesan yang ingin disembunyikan...", height=150)
        password = st.text_input("Password AES", type="password", placeholder="Masukkan password...")
        step_val = st.slider("Step Size DST", min_value=10, max_value=100, value=25,
                             help="Makin besar = lebih robust, PSNR sedikit turun")

        if st.button("Menyisipkan Data", type="primary", use_container_width=True):
            if not uploaded:
                st.error("Upload gambar cover dulu!")
            elif not message:
                st.error("Pesan tidak boleh kosong!")
            elif not password:
                st.error("Password tidak boleh kosong!")
            else:
                with st.spinner("Memproses..."):
                    try:
                        aes       = AESCipher(password)
                        stego     = StegoDST(step=float(step_val))
                        encrypted = aes.encrypt(message)

                        if len(encrypted) > stego.get_capacity(cover_img):
                            st.error(f"Pesan terlalu panjang! Maksimal ~{stego.get_capacity(cover_img) - 20} karakter.")
                        else:
                            stego_img        = stego.embed(cover_img, encrypted)
                            psnr_val, ssim_val = evaluate(cover_img, stego_img)

                            st.image(stego_img, caption="Stego Image", use_container_width=True)

                            m1, m2, m3 = st.columns(3)
                            m1.metric("PSNR", f"{psnr_val:.2f} dB",
                                      delta="Sangat Baik" if psnr_val > 40 else "Perlu diperbaiki")
                            m2.metric("SSIM", f"{ssim_val:.4f}",
                                      delta="Sangat Baik" if ssim_val > 0.95 else "Perlu diperbaiki")
                            m3.metric("Payload", f"{len(encrypted)} bytes")

                            buf = io.BytesIO()
                            Image.fromarray(stego_img).save(buf, format="PNG")
                            st.download_button(
                                "⬇Download Stego Image",
                                data=buf.getvalue(),
                                file_name="stego_image.png",
                                mime="image/png",
                                use_container_width=True
                            )
                            st.success("Embedding berhasil!")

                    except Exception as e:
                        st.error(f"Error: {e}")


# TAB EXTRACT
with tab_extract:
    st.subheader("Ambil Pesan dari Stego Image")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_stego = st.file_uploader(
            "Upload Stego Image",
            type=["png"],
            key="extract_upload",
            help="Gunakan file PNG hasil embed (jangan di-convert ke JPG!)"
        )
        if uploaded_stego:
            stego_loaded = np.array(Image.open(uploaded_stego).convert("RGB"))
            st.image(stego_loaded, caption="Stego Image", use_container_width=True)

    with col2:
        password_ex = st.text_input("Password AES", type="password",
                                     placeholder="Masukkan password yang sama saat embed...",
                                     key="extract_pass")
        step_ex     = st.slider("Step Size DST", min_value=10, max_value=100, value=25,
                                 help="Harus sama dengan saat embed!",
                                 key="extract_step")

        if st.button("Extract Sekarang", type="primary", use_container_width=True):
            if not uploaded_stego:
                st.error("Upload stego image dulu!")
            elif not password_ex:
                st.error("Password tidak boleh kosong!")
            else:
                with st.spinner("Mengekstrak pesan..."):
                    try:
                        aes       = AESCipher(password_ex)
                        stego     = StegoDST(step=float(step_ex))
                        extracted = stego.extract(stego_loaded)
                        decrypted = aes.decrypt(extracted)

                        st.success("Pesan berhasil diekstrak!")
                        st.text_area("Pesan Rahasia", value=decrypted, height=150)

                    except Exception as e:
                        st.error(f"Gagal mengekstrak: {e}")

        st.warning("Pastikan **password** dan **step size** sama persis dengan saat embed!")