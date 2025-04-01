# loader/pypdf2_loader.py

from PyPDF2 import PdfReader

def load_pdf(file_path: str) -> str:
    """
    PyPDF2를 사용하여 PDF 파일을 로드하고 전체 텍스트를 반환합니다.
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text
