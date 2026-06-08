from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


st.set_page_config(
    page_title="Ung dung trac nghiem",
    layout="centered",
)

st.title("Ung dung lam bai kiem tra trac nghiem")

st.write(
    """
    Day la ung dung Streamlit don gian giup ban tao cau hoi trac nghiem,
    tao bo tu vung, hoc va luyen noi truc tiep tren trinh duyet.
    """
)

st.info(
    "Dung menu ben trai de chon trang Them du lieu, Lam bai kiem tra hoac Hoc tu vung."
)

st.subheader("Chuc nang chinh")
st.markdown(
    """
    - Them cau hoi trac nghiem gom 4 dap an A, B, C, D.
    - Them tu vung gom tu tieng Anh va nghia tieng Viet.
    - Luu cau hoi vao `data/trac_nghiem/`.
    - Luu tu vung vao `data/tu_vung/`.
    - Lam bai kiem tra bang radio button.
    - Hoc tu vung theo chieu Anh - Viet hoac Viet - Anh.
    - Luyen noi bang ghi am, Whisper, IPA va Gemini feedback.
    - Cham diem, tinh diem thang 10 va hien thi chi tiet tung cau.
    """
)

st.caption(f"Thu muc du lieu: {BASE_DIR / 'data'}")
