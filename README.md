# Ung dung lam bai kiem tra va hoc tu vung

Day la ung dung Python + Streamlit dung de them cau hoi trac nghiem, them tu vung, lam bai kiem tra va hoc tu vung tren giao dien web don gian.

## Cau truc thu muc

```text
quiz-app/
|-- app.py
|-- data/
|   |-- trac_nghiem/
|   |   |-- questions.jsonl
|   |   |-- word_forms.jsonl
|   |   |-- tenses.jsonl
|   |   `-- phrasal_verbs.jsonl
|   |-- tu_vung/
|   |   |-- english_basic.jsonl
|   |   `-- english_advanced.jsonl
|   `-- sample_questions.jsonl
|-- src/
|   |-- __init__.py
|   |-- quiz_loader.py
|   |-- quiz_engine.py
|   |-- quiz_sets.py
|   |-- quiz_validator.py
|   |-- vocabulary_utils.py
|   `-- result_utils.py
|-- pages/
|   |-- 1_Them_cau_hoi.py
|   |-- 2_Lam_bai_kiem_tra.py
|   |-- 3_Hoc_tu_vung.py
|   `-- 4_Luyen_noi.py
|-- assets/
|   `-- README.md
|-- requirements.txt
|-- README.md
`-- .gitignore
```

## Cai thu vien

Nen tao moi truong ao truoc khi cai thu vien:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Chay app

```bash
streamlit run app.py
```

Sau khi chay lenh, Streamlit se hien thi dia chi local de mo app tren trinh duyet.

## Cau hinh Gemini API

Ung dung co the dung Gemini de giai thich dap an sai sau khi lam bai kiem tra.
Trang hoc tu vung co the dung mot Gemini API key rieng de hien thi phien am, va pinyin neu la tieng Trung.
Trang luyen noi co the dung mot Gemini API key rieng de tao feedback phat am.
Nut loa trong trang hoc tu vung dung Edge TTS de doc tu dang hoc, khong can API key.
Dat API key bang mot trong hai cach sau.

Cach 1: dung bien moi truong:

```bash
set GEMINI_API_KEY=your_api_key_here
set GEMINI_VOCABULARY_API_KEY=your_vocabulary_api_key_here
set GEMINI_SPEAKING_API_KEY=your_speaking_api_key_here
set GEMINI_MODEL=gemini-2.5-flash
set GEMINI_VOCABULARY_MODEL=gemini-2.5-flash-lite
set GEMINI_SPEAKING_MODEL=gemini-2.5-flash-lite
streamlit run app.py
```

Cach 2: tao file `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_api_key_here"
GEMINI_VOCABULARY_API_KEY = "your_vocabulary_api_key_here"
GEMINI_SPEAKING_API_KEY = "your_speaking_api_key_here"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_VOCABULARY_MODEL = "gemini-2.5-flash-lite"
GEMINI_SPEAKING_MODEL = "gemini-2.5-flash-lite"
```

Sau khi nop bai, voi cau tra loi sai, bam `AI giai thich dap an sai` de Gemini giai thich.
Khi hoc tu vung, bam `Xem phien am / pinyin` de Gemini hien thi phien am cua tu dang hoc.
Bam nut loa de tao va phat audio bang Edge TTS. File audio duoc cache trong `data/tts_cache/`.
Khi luyen noi, trang `Luyen noi` dung `faster-whisper` de nghe audio, `phonemizer` de tao IPA cho tieng Anh, `pypinyin` de tao pinyin cho tieng Trung va Gemini de tao feedback.
`phonemizer` can backend `espeak` tren may de tao IPA. Neu chua cai `espeak`, app se tu dung `GEMINI_SPEAKING_API_KEY` de tao IPA thay the.
Neu cai `espeak` o Windows, co the dat `PHONEMIZER_ESPEAK_LIBRARY` trong `.env`, vi du `PHONEMIZER_ESPEAK_LIBRARY=C:\Program Files\eSpeak NG\libespeak-ng.dll`.

## Dinh dang file JSONL

File trong `data/trac_nghiem/` luu moi cau hoi tren mot dong JSON rieng biet.

Vi du:

```jsonl
{"id": 1, "question": "Sau gioi tu, dong tu thuong o dang nao?", "options": {"A": "V-inf", "B": "To V", "C": "V-ing", "D": "V-ed"}, "answer": "C"}
```

Moi cau hoi gom:

- `id`: ma cau hoi
- `question`: noi dung cau hoi
- `options`: 4 dap an A, B, C, D
- `answer`: dap an dung, chi nhan A, B, C hoac D

File trong `data/tu_vung/` luu moi tu vung tren mot dong JSON rieng biet.

Vi du:

```jsonl
{"id": 1, "english": "apple", "vietnamese": "qua tao"}
```

Moi tu vung gom:

- `id`: ma tu vung
- `english`: tu tieng Anh
- `vietnamese`: nghia tieng Viet

## Quan ly nhieu bai kiem tra

Moi bai kiem tra duoc luu trong mot file JSONL rieng trong thu muc `data/trac_nghiem/`.
Moi bo tu vung duoc luu trong mot file JSONL rieng trong thu muc `data/tu_vung/`.
Danh sach bai kiem tra, bo tu vung va file tuong ung nam trong `src/quiz_sets.py`.

Vi du:

```python
QUIZ_FILES = {
    "Kiem tra V-ing / To V": "questions.jsonl",
    "Kiem tra tu loai": "word_forms.jsonl",
    "Kiem tra thi": "tenses.jsonl",
    "Kiem tra cum dong tu": "phrasal_verbs.jsonl",
}
```

Khi them cau hoi, chon bai kiem tra can luu. Khi them tu vung, chon bo tu vung can luu. Khi lam bai hoac hoc tu vung, ung dung se chi doc du lieu tu file tuong ung.

## Cach them cau hoi

1. Chay app bang lenh `streamlit run app.py`.
2. Chon trang `Them cau hoi` o menu ben trai.
3. Chon `Cau hoi trac nghiem`.
4. Chon bai kiem tra can luu.
5. Nhap noi dung cau hoi, 4 dap an va dap an dung.
6. Bam `Luu cau hoi`.

## Cach them tu vung

1. Chay app bang lenh `streamlit run app.py`.
2. Chon trang `Them cau hoi` o menu ben trai.
3. Chon `Tu vung`.
4. Chon bo tu vung can luu.
5. Nhap tu tieng Anh va nghia tieng Viet.
6. Bam `Luu tu vung`.

## Cach lam bai kiem tra

1. Chon trang `Lam bai kiem tra` o menu ben trai.
2. Doc tung cau hoi va chon dap an bang radio button.
3. Bam `Nop bai`.
4. Ung dung se hien thi tong so cau, so cau dung, so cau sai, diem thang 10 va chi tiet tung cau.

## Cach hoc tu vung

1. Chon trang `Hoc tu vung` o menu ben trai.
2. Chon bo tu vung.
3. Chon kieu hoc: hien tieng Anh nhap nghia tieng Viet, hoac hien nghia tieng Viet nhap tieng Anh.
4. Nhap dap an va bam `Kiem tra`.

## Cach luyen noi

1. Chon trang `Luyen noi` o menu ben trai.
2. Chon bo tu vung va tu/cau muc tieu.
3. Bam ghi am, doc tu/cau muc tieu, sau do bam `Phan tich phat am`.
4. Ung dung se hien thi transcript tu Whisper, IPA va feedback tu Gemini.

## Ghi chu

Logic doc/ghi file, validate du lieu, cham diem va dinh dang ket qua nam trong thu muc `src/`. Cac file Streamlit trong `app.py` va `pages/` chi phu trach giao dien va goi logic can thiet.
