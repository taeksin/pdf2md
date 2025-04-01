# loader/pdfplumber_loader.py

import pdfplumber

def load_pdf(file_path: str) -> str:
    """
    pdfplumber를 사용하여 PDF 파일을 로드하고 전체 텍스트를 반환합니다.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
