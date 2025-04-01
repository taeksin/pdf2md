# loader/pdfminer_loader.py

from pdfminer.high_level import extract_text

def load_pdf(file_path: str) -> str:
    """
    PDFMiner를 사용하여 PDF 파일을 로드하고 전체 텍스트를 반환합니다.
    
    Returns:
      문자열 (전체 텍스트)
    """
    text = extract_text(file_path)
    return text
