import streamlit as st
import re
import pandas as pd
from io import BytesIO
from docx import Document
import pdfplumber
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup

st.set_page_config(page_title="Universal Numerical Value Counter", page_icon="🔢")
st.title("🔢 Count Numerical Values in Any Document")

uploaded_file = st.file_uploader("Upload your document", 
                                 type=["txt", "csv", "xlsx", "docx", "pdf", "html", "jpg", "jpeg", "png"])

def extract_text(file):
    name = file.name.lower()

    if name.endswith(".txt"):
        return file.read().decode("utf-8")

    elif name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.to_string()

    elif name.endswith(".xlsx"):
        df = pd.read_excel(file)
        return df.to_string()

    elif name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif name.endswith((".jpg", ".jpeg", ".png")):
        image = Image.open(file)
        return pytesseract.image_to_string(image)

    elif name.endswith(".html"):
        soup = BeautifulSoup(file.read().decode("utf-8"), "lxml")
        return soup.get_text(separator=" ")

    else:
        return ""

def count_numbers(text):
    numbers = re.findall(r"[-+]?\d*[\.,]?\d+", text)
    return numbers

if uploaded_file:
    text = extract_text(uploaded_file)
    numbers = count_numbers(text)

    st.success(f"Total numeric values found: {len(numbers)}")

    if st.checkbox("Show extracted numbers"):
        st.dataframe(pd.DataFrame(numbers, columns=["Numbers"]))
