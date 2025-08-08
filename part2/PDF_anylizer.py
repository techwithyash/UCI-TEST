import os
import fitz  # PyMuPDF

def analyze_pdf(filepath):
    report = {"format": {}, "content": {}}
    if not filepath.lower().endswith(".pdf"):
        report["format"]["file_type"] = "fail"
        return report
    try:
        doc = fitz.open(filepath)
        report["format"]["file_type"] = "pass"
    except Exception:
        report["format"]["file_type"] = "fail"
        return report
    page = doc[0]
    fonts = set()
    font_sizes = set()
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                fonts.add(span["font"])
                font_sizes.add(round(span["size"]))
    report["format"]["font_family"] = "pass" if any("Times" in f for f in fonts) else "fail"
    report["format"]["font_size"] = "pass" if 12 in font_sizes else "fail"
    margin_pass = True
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, *_ = block
        if x0 < 72 or y0 < 72 or x1 > (page.rect.width - 72) or y1 > (page.rect.height - 72):
            margin_pass = False
            break
    report["format"]["margin"] = "pass" if margin_pass else "fail"
    section_limits = {
        "technical_requirements": (["technical requirements"], 8),
        "budget": (["budget"], 4),
        "qualification": (["qualification"], 4),
    }
    section_pages = {k: 0 for k in section_limits}
    found = {k: False for k in section_limits}
    current_section = None
    for i, page in enumerate(doc):
        text = page.get_text().lower()
        for sec, (keywords, _) in section_limits.items():
            if any(kw in text for kw in keywords):
                current_section = sec
                found[sec] = True
        if current_section:
            section_pages[current_section] += 1
    for sec, (_, max_pages) in section_limits.items():
        report["content"][f"{sec}_pages"] = section_pages[sec]
        report["content"][sec] = "pass" if section_pages[sec] > 0 and section_pages[sec] <= max_pages else "fail"
    return report

# --- Streamlit UI ---
import streamlit as st
import tempfile
import json

st.title("PDF Compliance Analyzer")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    result = analyze_pdf(tmp_path)
    st.subheader("Validation Report")
    st.json(result)
    os.remove(tmp_path)