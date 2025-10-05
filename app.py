# app_sum_numbers.py
import streamlit as st
import re
import pandas as pd
from io import BytesIO
from docx import Document
import pdfplumber
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup

st.set_page_config(page_title="Sum numbers in any document", page_icon="🔢")
st.title("🔢 Sum numeric values in any document")

uploaded_file = st.file_uploader("Upload document", type=["txt","csv","xlsx","docx","pdf","html","jpg","jpeg","png"])

# ---------- text extraction ----------
def extract_text(file):
    name = file.name.lower()
    data = file.read()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    elif name.endswith(".csv"):
        df = pd.read_csv(BytesIO(data))
        return df.to_string()
    elif name.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(data), engine="openpyxl")
        return df.to_string()
    elif name.endswith(".docx"):
        doc = Document(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs])
    elif name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text
    elif name.endswith((".jpg","jpeg","png")):
        image = Image.open(BytesIO(data))
        return pytesseract.image_to_string(image)
    elif name.endswith(".html"):
        soup = BeautifulSoup(data.decode("utf-8", errors="ignore"), "lxml")
        return soup.get_text(separator=" ")
    else:
        return ""

# ---------- numeric extraction & parsing ----------
def extract_numbers_and_sum(text, percent_as_fraction=False, ignore_page_numbers=True):
    # robust-ish regex to catch integers, decimals, scientific notation, optional %
    pattern = re.compile(r'([-+]?\d[\d,\.]*?(?:[eE][-+]?\d+)?%?)')
    results = []
    for m in pattern.finditer(text):
        token = m.group(1)
        start, end = m.span(1)

        # context check to ignore page numbers or footers (simple heuristic)
        if ignore_page_numbers:
            context = text[max(0,start-30): min(len(text), end+30)]
            if re.search(r'\bpage\b|\bpg\b', context, flags=re.I):
                continue

        # normalize token
        s = token.strip().replace('−','-')  # handle unicode minus
        is_percent = s.endswith('%')
        # remove currency symbols/letters around
        s_clean = re.sub(r'[^\d\.\-eE+,%]', '', s)  # keep digits, ., -, e, E, +, comma, %
        # remove commas (thousands separators)
        s_clean = s_clean.replace(',', '')

        # if only a '%' left or empty after cleaning, skip
        if s_clean in ['', '%', '+', '-']:
            continue

        try:
            if is_percent:
                num = float(s_clean.replace('%',''))
                if percent_as_fraction:
                    num = num / 100.0
            else:
                num = float(s_clean)
            results.append((token, num, start, end))
        except Exception:
            # fallback: try to strip non-digit chars and parse
            s_try = re.sub(r'[^\d\.\-eE+]', '', s_clean)
            try:
                num = float(s_try)
                results.append((token, num, start, end))
            except Exception:
                continue

    # produce summary
    numbers_only = [r[1] for r in results]
    total = sum(numbers_only) if numbers_only else 0.0
    stats = {
        "count": len(numbers_only),
        "sum": total,
        "min": min(numbers_only) if numbers_only else None,
        "max": max(numbers_only) if numbers_only else None,
        "mean": (sum(numbers_only)/len(numbers_only)) if numbers_only else None
    }
    return results, stats

# ---------- UI ----------
if uploaded_file:
    st.info("Extracting text...")
    text = extract_text(uploaded_file)
    if not text.strip():
        st.error("No text extracted from this file (PDF might be scanned or content is non-text).")
    else:
        percent_as_fraction = st.checkbox("Interpret percents as fractions (10% → 0.10)", value=False)
        ignore_pages = st.checkbox("Ignore page/footer numbers (heuristic)", value=True)
        results, stats = extract_numbers_and_sum(text, percent_as_fraction, ignore_pages)

        st.success(f"Found {stats['count']} numeric tokens — Sum = {stats['sum']}")
        st.write("Statistics:", stats)

        if st.checkbox("Show extracted tokens and parsed values"):
            df = pd.DataFrame([{"raw": r[0], "value": r[1], "start": r[2], "end": r[3]} for r in results])
            st.dataframe(df)

        if st.checkbox("Show a few context snippets (for debugging)"):
            snippets = []
            for raw, val, start, end in results[:50]:
                left = max(0, start-30)
                right = min(len(text), end+30)
                snippets.append({"raw": raw, "value": val, "context": text[left:right].replace("\n"," ")})
            st.dataframe(pd.DataFrame(snippets))
